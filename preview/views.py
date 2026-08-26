import io
from django.shortcuts import render
from .analyzer import HRISAnalyzer

def preview_import(request):
    context = {}
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        try:
            # Decode with utf-8-sig to automatically handle Byte Order Marks
            decoded_file = csv_file.read().decode('utf-8-sig')
            io_string = io.StringIO(decoded_file)
            
            analyzer = HRISAnalyzer(io_string)
            analyzer.analyze()
            
            # Prepare presentation data
            context['analyzed'] = True
            context['total_rows'] = analyzer.total_rows
            context['accepted_count'] = len(analyzer.accepted_employees)
            context['errors'] = analyzer.errors
            
            context['roots'] = [
                analyzer.accepted_employees[r_id] 
                for r_id in analyzer.roots
            ]
            
            managers = []
            for mgr_id, reports in analyzer.manager_relationships.items():
                managers.append({
                    "employee_name": analyzer.accepted_employees[mgr_id].get("employee_name", ""),
                    "email": analyzer.accepted_employees[mgr_id].get("email", ""),
                    "report_count": len(reports)
                })
            managers.sort(key=lambda x: x['report_count'], reverse=True)
            context['managers'] = managers
            
            context['cycles'] = [
                analyzer.accepted_employees[c_id]
                for c_id in analyzer.cycle_members
            ]
            
        except Exception as e:
            context['fatal_error'] = f"Failed to process file: {str(e)}"
            
    return render(request, 'preview/index.html', context)