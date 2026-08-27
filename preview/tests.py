import io
from django.test import SimpleTestCase
from .analyzer import HRISAnalyzer

class HRISAnalyzerTests(SimpleTestCase):
    def test_duplicate_identity_exclusion(self):
        csv_data = (
            "employee_id,employee_name,email,manager_id,manager_email\n"
            "1,Alice,alice@div.com,,\n"
            "2,Bob,bob@div.com,1,alice@div.com\n"
            "2,Bob Clone,bob@div.com,1,alice@div.com\n"
        )
        analyzer = HRISAnalyzer(io.StringIO(csv_data))
        analyzer.analyze()
        
        self.assertEqual(analyzer.total_rows, 3)
        self.assertIn("1", analyzer.accepted_employees)
        # Both Bob rows share an ID/Email and must be totally excluded
        self.assertNotIn("2", analyzer.accepted_employees)
        self.assertTrue(any("Duplicate" in err for err in analyzer.errors))

    def test_cycle_detection(self):
        # 1 -> 3, 3 -> 2, 2 -> 1 (Cycle of 1, 2, 3)
        # 4 -> 1 (Reports into cycle, but is NOT part of the cycle itself)
        csv_data = (
            "employee_id,email,manager_id\n"
            "1,a@d.com,3\n"
            "2,b@d.com,1\n"
            "3,c@d.com,2\n"
            "4,d@d.com,1\n"
        )
        analyzer = HRISAnalyzer(io.StringIO(csv_data))
        analyzer.analyze()
        
        self.assertEqual(len(analyzer.accepted_employees), 4)
        self.assertSetEqual(analyzer.cycle_members, {"1", "2", "3"})
        self.assertNotIn("4", analyzer.cycle_members)

    def test_manager_error_source_row_number(self):
        csv_data = (
            "employee_id,employee_name,email,manager_id\n" 
            "1,Alice,alice@div.com,\n"                   
            "2,Bob,bob@div.com,999\n"                    
        )
        analyzer = HRISAnalyzer(io.StringIO(csv_data))
        analyzer.analyze()
        
        self.assertTrue(any("Row 3: Manager ID '999' not found." in err for err in analyzer.errors))

    def test_blank_lines_preserve_row_numbers(self):
        csv_data = (
            "employee_id,employee_name,email,manager_id,manager_email\n" # Line 1
            "1,Alice,alice@x.com,,\n"                                    # Line 2
            "\n"                                                         # Line 3 (Blank)
            "2,Bob,,,\n"                                                 # Line 4 (Missing email)
        )
        analyzer = HRISAnalyzer(io.StringIO(csv_data))
        analyzer.analyze()
        
        # Proves that despite line 3 being blank, Bob is correctly identified on Line 4
        self.assertTrue(any("Row 4: Missing required employee_id or email." in err for err in analyzer.errors))


    def test_incomplete_row_does_not_poison_valid_id(self):
        csv_data = (
            "employee_id,employee_name,email,manager_id,manager_email\n"
            "1,Alice,alice@x.com,,\n"
            "1,,,,\n" 
        )
        analyzer = HRISAnalyzer(io.StringIO(csv_data))
        analyzer.analyze()
        self.assertIn("1", analyzer.accepted_employees)
        self.assertTrue(any("Row 3: Missing required employee_id or email." in err for err in analyzer.errors))
        self.assertFalse(any("Duplicate employee_id" in err for err in analyzer.errors))

    def test_incomplete_row_does_not_poison_valid_email(self):
        csv_data = (
            "employee_id,employee_name,email,manager_id,manager_email\n"
            "1,Alice,alice@x.com,,\n"
            ",,alice@x.com,,\n" 
        )
        analyzer = HRISAnalyzer(io.StringIO(csv_data))
        analyzer.analyze()
        self.assertIn("1", analyzer.accepted_employees)
        self.assertTrue(any("Row 3: Missing required employee_id or email." in err for err in analyzer.errors))
        self.assertFalse(any("Duplicate email" in err for err in analyzer.errors))

    def test_malformed_extra_column_rejected(self):
        csv_data = (
            "employee_id,employee_name,email,manager_id,manager_email\n"
            "1,Smith, Jane,smith@x.com,,\n" 
        )
        analyzer = HRISAnalyzer(io.StringIO(csv_data))
        analyzer.analyze()
        self.assertNotIn("1", analyzer.accepted_employees)
        self.assertTrue(any("Row 2: Malformed CSV row" in err for err in analyzer.errors))

    def test_valid_quoted_comma_accepted(self):
        csv_data = (
            "employee_id,employee_name,email,manager_id,manager_email\n"
            '1,"Smith, Jane",smith@x.com,,\n' 
        )
        analyzer = HRISAnalyzer(io.StringIO(csv_data))
        analyzer.analyze()
        self.assertIn("1", analyzer.accepted_employees)
        self.assertEqual(analyzer.accepted_employees["1"]["employee_name"], "Smith, Jane")
        self.assertFalse(any("Malformed CSV row" in err for err in analyzer.errors))