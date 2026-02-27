from flask import Flask, render_template_string, request, send_file
import pdfplumber
import pandas as pd
import re
import os

app = Flask(__name__)

PASSWORD = "Monu@vipin84"

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Secure Bank Analyzer</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{
  font-family:Arial;
  background:#f4f6f9;
  padding:30px;
}
.card{
  background:white;
  padding:25px;
  border-radius:12px;
  max-width:400px;
  margin:auto;
  box-shadow:0 5px 20px rgba(0,0,0,0.1);
}
input,button{
  width:100%;
  padding:12px;
  margin-top:10px;
}
button{
  background:#007bff;
  color:white;
  border:none;
  border-radius:8px;
}
</style>
</head>
<body>
<div class="card">
<h2>🔐 MSME Bank Analyzer</h2>
{% if not logged_in %}
<form method="POST">
<input type="password" name="password" placeholder="Enter Password" required>
<button type="submit">Login</button>
</form>
{% else %}
<form method="POST" enctype="multipart/form-data">
<input type="file" name="file" required>
<button type="submit">Upload & Process</button>
</form>
{% endif %}
</div>
</body>
</html>
"""

def clean_name(text):
    text = text.upper()
    text = re.sub(r'UPI/|IMPS/|NEFT|RTGS|POS|ATM|MOB/|TPFT/|P2A/|P2M/', '', text)
    text = re.sub(r'\d+', '', text)
    parts = re.split(r'[-/]', text)
    return parts[-1].strip()

@app.route("/", methods=["GET","POST"])
def home():
    if request.method == "POST":
        if "password" in request.form:
            if request.form["password"] == PASSWORD:
                return render_template_string(HTML, logged_in=True)
            else:
                return "Wrong Password ❌"

        if "file" in request.files:
            file = request.files["file"]
            file.save("statement.pdf")

            transactions = []

            with pdfplumber.open("statement.pdf") as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table:
                        for row in table:
                            if row:
                                row_text = " ".join([str(x) for x in row if x])

                                date_match = re.search(r'\d{2}[-/]\d{2}[-/]\d{4}', row_text)
                                if not date_match:
                                    continue

                                date = date_match.group()
                                amounts = re.findall(r'\d{1,3}(?:,\d{3})*\.\d{2}', row_text)

                                if len(amounts) >= 2:
                                    balance = float(amounts[-1].replace(',', ''))
                                    amt = float(amounts[-2].replace(',', ''))

                                    debit = 0
                                    credit = 0

                                    if "CR" in row_text or "CREDIT" in row_text:
                                        credit = amt
                                    else:
                                        debit = amt

                                    name = clean_name(row_text)
                                    transactions.append([date, name, debit, credit, balance])

            df = pd.DataFrame(transactions, columns=["Date","Name","Debit","Credit","Balance"])
            df.to_excel("All_Transactions.xlsx", index=False)

            os.remove("statement.pdf")

            return send_file("All_Transactions.xlsx", as_attachment=True)

    return render_template_string(HTML, logged_in=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
