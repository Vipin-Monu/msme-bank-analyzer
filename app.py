from flask import Flask, render_template_string, request, send_file
import pdfplumber
import pandas as pd
import os
import re

app = Flask(__name__)

PASSWORD = "1234"   # simple password for now

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bank Analyzer</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="font-family:Arial;text-align:center;padding:40px;">

<h2>Bank Statement Analyzer</h2>

<form method="POST" enctype="multipart/form-data">
<input type="password" name="password" placeholder="Enter Password" required><br><br>
<input type="file" name="file" accept=".pdf" required><br><br>
<button type="submit">Upload & Convert</button>
</form>

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        if request.form["password"] != PASSWORD:
            return "Wrong Password"

        file = request.files["file"]
        file.save("statement.pdf")

        data = []

        with pdfplumber.open("statement.pdf") as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines = text.split("\n")
                    for line in lines:
                        match = re.search(r'(\d{2}/\d{2}/\d{4}).*?(-?\d+\.\d{2})$', line)
                        if match:
                            date = match.group(1)
                            amount = match.group(2)
                            data.append([date, amount])

        df = pd.DataFrame(data, columns=["Date", "Amount"])
        df.to_excel("All_Transactions.xlsx", index=False)

        os.remove("statement.pdf")

        return send_file("All_Transactions.xlsx", as_attachment=True)

    return render_template_string(HTML)


if __name__ == "__main__":
    app.run()
