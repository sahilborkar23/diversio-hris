import csv
from collections import defaultdict

class HRISAnalyzer:
    def __init__(self, file_stream):
        self.file_stream = file_stream
        self.total_rows = 0
        self.errors = []
        self.accepted_employees = {}
        self.roots = []
        self.manager_relationships = defaultdict(list)
        self.cycle_members = set()

    def analyze(self):
        reader = csv.DictReader(self.file_stream)
        raw_rows = []
        
        # 1. Parsing and Normalization
        for row_num, row in enumerate(reader, start=2): # Start at 2 to account for header
            self.total_rows += 1
            normalized = {}
            for key, value in row.items():
                if key:
                    normalized[key.strip()] = value.strip() if value else ''
            raw_rows.append((row_num, normalized))

        # 2. Duplicate Detection Prep
        id_counts = defaultdict(int)
        email_counts = defaultdict(int)
        
        for _, row in raw_rows:
            emp_id = row.get('employee_id', '')
            email = row.get('email', '').lower()
            if emp_id: id_counts[emp_id] += 1
            if email: email_counts[email] += 1

        # 3. Identity Validation
        valid_employees = {}
        email_to_id = {}
        
        for row_num, row in raw_rows:
            emp_id = row.get('employee_id', '')
            email = row.get('email', '').lower()
            
            if not emp_id or not email:
                self.errors.append(f"Row {row_num}: Missing required employee_id or email.")
                continue
                
            if id_counts[emp_id] > 1:
                self.errors.append(f"Row {row_num}: Duplicate employee_id '{emp_id}'. Row excluded.")
                continue
                
            if email_counts[email] > 1:
                self.errors.append(f"Row {row_num}: Duplicate email '{email}'. Row excluded.")
                continue
                
            # Normalize relevant fields in the dictionary
            row['email'] = email
            row['manager_email'] = row.get('manager_email', '').lower()
            
            valid_employees[emp_id] = row
            email_to_id[email] = emp_id

        self.accepted_employees = valid_employees

        # 4. Manager Resolution & Hierarchy Build
        for emp_id, row in valid_employees.items():
            mgr_id_raw = row.get('manager_id', '')
            mgr_email_raw = row.get('manager_email', '')
            
            if not mgr_id_raw and not mgr_email_raw:
                self.roots.append(emp_id)
                continue
                
            resolved_by_id = mgr_id_raw if mgr_id_raw in valid_employees else None
            resolved_by_email = email_to_id.get(mgr_email_raw) if mgr_email_raw else None
            
            final_mgr_id = None
            has_error = False
            
            # Resolve according to assignment rules
            if mgr_id_raw and mgr_email_raw:
                if not resolved_by_id or not resolved_by_email:
                    self.errors.append(f"Row for {emp_id}: Manager not found.")
                    has_error = True
                elif resolved_by_id != resolved_by_email:
                    self.errors.append(f"Row for {emp_id}: Conflicting manager references.")
                    has_error = True
                else:
                    final_mgr_id = resolved_by_id
            elif mgr_id_raw:
                if not resolved_by_id:
                    self.errors.append(f"Row for {emp_id}: Manager ID '{mgr_id_raw}' not found.")
                    has_error = True
                else:
                    final_mgr_id = resolved_by_id
            elif mgr_email_raw:
                if not resolved_by_email:
                    self.errors.append(f"Row for {emp_id}: Manager email '{mgr_email_raw}' not found.")
                    has_error = True
                else:
                    final_mgr_id = resolved_by_email

            if final_mgr_id == emp_id:
                self.errors.append(f"Row for {emp_id}: Employee cannot manage themselves.")
                has_error = True
                final_mgr_id = None

            # Record relationships for valid managers
            if final_mgr_id and not has_error:
                self.manager_relationships[final_mgr_id].append(emp_id)
                row['_resolved_manager_id'] = final_mgr_id # Store for graph traversal

        # 5. Cycle Detection
        self._detect_cycles(valid_employees)

    def _detect_cycles(self, valid_employees):
        global_visited = set()
        
        for emp_id in valid_employees:
            if emp_id in global_visited:
                continue
                
            local_visited = set()
            local_path = []
            current = emp_id
            
            while current:
                if current in local_visited:
                    cycle_start_idx = local_path.index(current)
                    for cycle_node in local_path[cycle_start_idx:]:
                        self.cycle_members.add(cycle_node)
                    break
                    
                if current in global_visited:
                    break
                    
                local_visited.add(current)
                local_path.append(current)
                
                # Traverse up to manager
                current = valid_employees[current].get('_resolved_manager_id')
                
            for node in local_path:
                global_visited.add(node)