from flask import Flask, request, make_response, jsonify, render_template_string
from xhtml2pdf import pisa
from io import BytesIO
from datetime import datetime
from openpyxl import Workbook
from num2words import num2words
app = Flask(__name__)
@app.route('/')
def getroute():
    return "hello world"
@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        payload = request.get_json()
        project = payload.get("project", "Unnamed Project")
        client_name = payload.get("clientName", "Unknown Client")
        subworks = payload.get("subworks", [])

        subworks_html = ""
        grand_total = 0
        unit=""
        for idx, subwork in enumerate(subworks, start=1):
            name = subwork.get("name", "Unnamed Subwork")
            default_sft = subwork["default"].get("SFT", 0)
            default_cft = subwork["default"].get("CFT", 0)
            details = subwork.get("details", [])
            reductions = subwork.get("reductions", [])

            details_rows = ""
            total_quantity = 0
            r=0
            for count, d in enumerate(details, start=1):
                if default_sft > 0:
                    r=default_sft
                    unit="SFT"
                    quantity = d['length'] * d['breadth'] * d['number']
                elif default_cft > 0:
                    r=default_cft
                    unit="CFT"
                    quantity = d['length'] * d['breadth'] * d['depth'] * d['number']
                else:
                    quantity = 0  
                total_quantity += quantity
                details_rows += f"<tr><td>{count}</td><td>{d['name']}</td><td>{d['number']}</td>" \
                                f"<td>{d['length']}</td><td>{d['breadth']}</td><td>{d['depth']}</td>" \
                                f"<td>{quantity:.2f}</td><td>-</td><td>-</td></tr>"                                
            
            details_rows += f"<tr><td colspan='6' style='text-align: center;'>-</td>" \
                   f"<td><strong>{(total_quantity):.2f}</strong></td><td>-</td><td>-</td></tr>"

            
            details_rows += f"<tr><td>Deduction</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td></tr>"

            reduction_quantity = 0
            reductions_rows = ""
            rr=0
            for count, r in enumerate(reductions, start=1):
                if default_sft > 0:
                    rr=default_sft
                    unit="SFT"
                    quantity = r['length'] * r['breadth'] * r['number']
                elif default_cft > 0:
                    rr=default_cft
                    unit="CFT"
                    quantity = r['length'] * r['breadth'] * r['depth'] * r['number']
                else:
                    quantity = 0
                reduction_quantity += quantity
                details_rows += f"<tr><td>{count}</td><td>{r['name']}</td><td>{r['number']}</td>" \
                                   f"<td>{r['length']}</td><td>{r['breadth']}</td><td>{r['depth']}</td>" \
                                   f"<td>{quantity:.2f}</td><td>-</td><td>-</td></tr>"
            details_rows += f"<tr><td colspan='6' style='text-align: center;'>-</td>" \
                   f"<td><strong>{(reduction_quantity):.2f}</strong></td><td>-</td><td>-</td></tr>"

            
            net_quantity = total_quantity - reduction_quantity
            rate=0
            if default_cft>0:
                rate=default_cft
            if default_sft>0:
                rate=default_sft
           
            total_cost = net_quantity * rate
            grand_total += total_cost
            gt = f"{grand_total:.2f}"
            GrandInWords=num2words(gt)
            details_rows += f"<tr><td colspan='6' style='text-align: center;'>Total</td>" \
                   f"<td><strong>{(net_quantity):.2f}</strong></td><td><strong>{rate} Rs. / {unit}</strong></td><td><strong>Rs. {(net_quantity) * rate:.2f}</strong></td></tr>"

            
            subworks_html += f"""
            <h3>{idx}. {name}</h3>
            <p>Default SFT: {default_sft}, Default CFT: {default_cft}</p>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
                <thead>
                    <tr>
                        <th>S.No</th><th>Name</th><th>Number</th>
                        <th>Length(ft)</th><th>Breadth(ft)</th><th>Depth(ft)</th><th>Quantity</th><th>Unit(SFT/CFT)</th><th>Total (Rs.)</th>
                    </tr>
                </thead>
                <tbody>
                    {details_rows if details else '<tr><td colspan="9" style="text-align: center;">No details available</td></tr>'}
                </tbody>
            </table>
           
            
            """
# <p>Total Quantity: {total_quantity:.2f}</p>

#             <p> Deductions: <strong>{reduction_quantity:.2f}</strong></p>
#             <p> Net Quantity: <strong>{net_quantity:.2f}</strong></p>
#             <p>Total Cost: <strong>Rs. {total_cost:.2f}</strong></p>
      
        html_content = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                th, td {{
                    border: 1px solid black;
                    padding: 5px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                h1, h3 {{
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <h1>{project}</h1>
            <span>ABC Company </span>
            <p><strong>Project Name:</strong> {project}</p>
            <p><strong>Client Name:</strong> {client_name}</p>
            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
            {subworks_html}
            <h2>Grand Total :<strong> Rs. {grand_total:.2f}</strong></h2>
            <h2>Grand Total :<strong>Rs. {GrandInWords} Only</strong></h2>
        </body>
        </html>
        """

        
        pdf = BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf)
        pdf.seek(0)

        if pisa_status.err:
            return {"error": "Error in PDF generation"}, 500

        
        response = make_response(pdf.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=report.pdf'
        return response

    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/generate-pdf-subwork', methods=['POST'])
def generate_pdf_subwork():
    payload = request.get_json()

    # Extract project data
    project_name = payload.get("project", "N/A")
    client_name = payload.get("clientName", "N/A")
    work = payload.get("work", "N/A")
    subworks = payload.get("subworks", {})
    details = subworks.get("details", [])
    default_value = subworks.get("default", {})
    default_sft = default_value.get("SFT", 0)
    default_cft = default_value.get("CFT", 0)
    reductions = subworks.get("reductions", [])

    details_rows = ""
    total_quantity = 0

    grand_total = 0
    rate=0
    if default_sft!=0:
        rate=default_sft
    
    if default_cft!=0:
        rate=default_cft
    
    # Generate details rows
    for idx, subwork in enumerate(details, start=1):
        quantity=0
        if default_sft!=0:
            quantity=subwork.get("number")*subwork.get("length")*subwork.get("breadth")
        
        if default_cft!=0:
            quantity=subwork.get("number")*subwork.get("length")*subwork.get("breadth")*subwork.get("depth")
        
        # rate = default_sft if subwork.get("breadth", 0) * subwork.get("depth", 0) > 0 else default_cft
        total = rate * quantity
        total_quantity += quantity
        grand_total += total

        details_rows += f"""
            <tr>
                <td>{idx}</td>
                <td>{subwork.get('name', 'Unnamed')}</td>
                <td>{subwork.get('number', 0)}</td>
                <td>{subwork.get('length', 0)}</td>
                <td>{subwork.get('breadth', 0)}</td>
                <td>{subwork.get('depth', 0)}</td>
                <td>{quantity:.2f}</td>
                <td>-</td>
                <td>-</td>
            </tr>
        """
    details_rows += f"<tr><td colspan='6' style='text-align: center;'>-</td>" \
                   f"<td><strong>{(total_quantity):.2f}</strong></td><td>-</td><td>-</td></tr>"

    details_rows += f"""
        <tr>
             <td><h3>Deductions</h3></td>
             <td>-</td>
             <td>-</td>
             <td>-</td>
             <td>-</td>
             <td>-</td>
             <td>-</td>
             <td>-</td>
             <td>-</td>
        </tr>
    """
    
    reduction_quantity = 0
    reduction_rows=""
    for idx, subwork in enumerate(reductions, start=1):
        quantity=0
        if default_sft!=0:
            quantity=subwork.get("number")*subwork.get("length")*subwork.get("breadth")
        
        if default_cft!=0:
            quantity=subwork.get("number")*subwork.get("length")*subwork.get("breadth")*subwork.get("depth")
        
        # rate = default_sft if subwork.get("breadth", 0) * subwork.get("depth", 0) > 0 else default_cft
        total = rate * quantity
        reduction_quantity += quantity
        grand_total += total
        details_rows += f"""
            <tr>
                <td>{idx}</td>
                <td>{subwork.get('name', 'Unnamed')}</td>
                <td>{subwork.get('number', 0)}</td>
                <td>{subwork.get('length', 0)}</td>
                <td>{subwork.get('breadth', 0)}</td>
                <td>{subwork.get('depth', 0)}</td>
                <td>{quantity:.2f}</td>
                <td>-</td>
                <td>-</td>
            </tr>
        """
    details_rows += f"<tr><td colspan='6' style='text-align: center;'>-</td>" \
                   f"<td><strong>{(reduction_quantity):.2f}</strong></td><td>-</td><td>-</td></tr>"

    # Add totals row
    details_rows += f"""
        <tr>
            <td colspan="6" style="text-align: center;">Total</td>
            <td>{(total_quantity-reduction_quantity):.2f}</td>
            <td>{rate}</td>
            <td><strong>Rs. {(total_quantity-reduction_quantity)*rate:.2f}</strong></td>
        </tr>
     """
    GD=f"{(total_quantity-reduction_quantity)*rate:.2f}"
    GDNUM=num2words(GD)
    subworks_html = f"""
        <p>Default SFT: {default_sft}, Default CFT: {default_cft}</p>
        <table>
            <thead>
                <tr>
                    <th>S.No</th>
                    <th>Name</th>
                    <th>Number</th>
                    <th>Length (ft)</th>
                    <th>Breadth (ft)</th>
                    <th>Depth (ft)</th>
                    <th>Quantity</th>
                    <th>Rate</th>
                    <th>Total (Rs.)</th>
                </tr>
            </thead>
            <tbody>
                {details_rows}
            </tbody>
        </table>
        
        <h2>Grand Total: <strong>Rs. {(total_quantity-reduction_quantity)*rate:.2f}</strong></h2>
        
            <h2>Grand Total :<strong>Rs. {GDNUM} Only</strong></h2>
    """

    html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ border: 1px solid black; padding: 5px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>{project_name}</h1>
            <h2>Work Name : {work}</h2>
            <h2>SubWork Name : {subwork.get("name") }</h2>

            <span>ABC Company </span>
            <p><strong>Project Name:</strong> {project_name}</p>
            <p><strong>Client Name:</strong> {client_name}</p>
            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
            {subworks_html}
        </body>
        </html>
    """
     
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf)
    pdf.seek(0)

    if pisa_status.err:
        return {"error": "Error in PDF generation"}, 500

    
    response = make_response(pdf.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=report.pdf'
    return response

@app.route('/generate-xlsx-subwork', methods=['POST'])
def generate_xlsx_subwork():
    try:
        payload = request.get_json()

        # Extract project data
        project_name = payload.get("project", "N/A")
        client_name = payload.get("clientName", "N/A")
        work = payload.get("work", "N/A")
        subworks = payload.get("subworks", {})
        details = subworks.get("details", [])
        default_value = subworks.get("default", {})
        default_sft = default_value.get("SFT", 0)
        default_cft = default_value.get("CFT", 0)
        reductions = subworks.get("reductions", [])
        subworkName=subworks.get("name")
        # Create an Excel workbook and sheet
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Subwork Report"

        # Add header
        sheet.append([f"Project Name: {project_name}"])
        sheet.append([f"Client Name: {client_name}"])
        sheet.append([f"Work Name: {work}"])
        sheet.append([f"SubWork Name:{subworkName}"])
        sheet.append([f"Date: {datetime.now().strftime('%Y-%m-%d')}"])
        sheet.append([])

        # Add table headers for details
        headers = ["S.No", "Name", "Number", "Length (ft)", "Breadth (ft)", "Depth (ft)", "Quantity", "Rate", "Total (Rs.)"]
        sheet.append(headers)

        # Add details rows
        total_quantity = 0
        grand_total = 0
        rate = default_sft if default_sft != 0 else default_cft
        unit = "SFT" if default_sft != 0 else "CFT"
        for idx, subwork in enumerate(details, start=1):
            quantity = subwork.get("number") * subwork.get("length") * subwork.get("breadth")
            if default_cft != 0:
                quantity *= subwork.get("depth", 1)

            total = rate * quantity
            total_quantity += quantity
            grand_total += total

            sheet.append([
                idx,
                subwork.get("name", "Unnamed"),
                subwork.get("number", 0),
                subwork.get("length", 0),
                subwork.get("breadth", 0),
                subwork.get("depth", 0),
                round(quantity, 2),
                
                "",
                ""
                # round(total, 2)
            ])

        # Add total row
        # sheet.append(["", "", "", "", "", "Total", f"{round(total_quantity, 2)+""+unit}", "", ""])
        sheet.append(["", "", "", "", "", "Total", round(total_quantity, 2), unit, ""])
        sheet.append([])

        # Add reduction rows
        sheet.append(["Deductions"])
        # sheet.append(headers)
        reduction_quantity = 0

        for idx, subwork in enumerate(reductions, start=1):
            quantity = subwork.get("number") * subwork.get("length") * subwork.get("breadth")
            if default_cft != 0:
                quantity *= subwork.get("depth", 1)

            total = rate * quantity
            reduction_quantity += quantity

            sheet.append([
                idx,
                subwork.get("name", "Unnamed"),
                subwork.get("number", 0),
                subwork.get("length", 0),
                subwork.get("breadth", 0),
                subwork.get("depth", 0),
                round(quantity, 2),
                
                "",
                "",
                # round(total, 2)
            ])
        sheet.append(["", "", "", "", "", "Total", round(reduction_quantity, 2), unit, ""])
        # Add total reduction row
        sheet.append([])
        sheet.append(["", "", "", "", "", "Total",  round((total_quantity - reduction_quantity)),f"{rate} R.s/{unit}", round((total_quantity - reduction_quantity)*rate, 2)])

        # Grand total
        # sheet.append([f"Net Quantity : {round((total_quantity - reduction_quantity), 2)}"])
        GD=f"{round((total_quantity - reduction_quantity) * rate, 2)}"
        GDNUM=num2words(GD)
        sheet.append([f"Grand Total (Rs.): {round((total_quantity - reduction_quantity) * rate, 2)}"])
        sheet.append([f"Rupees {GDNUM} Only"])

        # Save Excel to a BytesIO stream
        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        # Create a response with the Excel file
        response = make_response(output.read())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = 'attachment; filename=subwork_report.xlsx'

        return response

    except Exception as e:
        return {"error": str(e)}, 500
if __name__ == '__main__':
    app.run(debug=True)
