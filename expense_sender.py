import smtplib
import os
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ── Load Data ────────────────────────────────────────────────────────────────
df = pd.read_csv("expenses.csv", sep="\t")  # 👈 tab separator
df["Date"] = pd.to_datetime(df["Date"], format="%d-%b-%y")  # 👈 %y for 2-digit year
df["Amount"] = pd.to_numeric(df["Amount"])

# ── Filter Last Month ────────────────────────────────────────────────────────
today = datetime.today()
last_month = today.month - 1 if today.month > 1 else 12
last_year  = today.year if today.month > 1 else today.year - 1

filtered_df = df[
    (df["Date"].dt.month == last_month) &
    (df["Date"].dt.year  == last_year)
].copy()

filtered_df["Date"]   = filtered_df["Date"].dt.strftime("%d-%b-%Y")
filtered_df["Amount"] = filtered_df["Amount"].apply(lambda x: f"₹{x:,.0f}")

total = df[
    (df["Date"].dt.month == last_month) &
    (df["Date"].dt.year  == last_year)
]["Amount"].sum()

month_name = datetime(last_year, last_month, 1).strftime("%B %Y")

# ── Build HTML ───────────────────────────────────────────────────────────────
def build_html(df, total, month_name):
    if df.empty:
        return f"<p>No expenses found for {month_name}.</p>"

    rows = ""
    for _, row in df.iterrows():
        rows += f"""
        <tr>
            <td>{row['Date']}</td>
            <td>{row['Category']}</td>
            <td>{row['Description']}</td>
            <td><b>{row['Amount']}</b></td>
        </tr>"""

    return f"""
    <html><body>
    <p>Dear Team,</p>
    <p>Please find the <b>Monthly Expense Report for {month_name}</b> below:</p>
    <table border="1" cellpadding="6" cellspacing="0"
           style="border-collapse:collapse; font-family:Arial; font-size:13px;">
        <thead style="background-color:#2196F3; color:white;">
            <tr>
                <th>Date</th>
                <th>Category</th>
                <th>Description</th>
                <th>Amount</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
        <tfoot>
            <tr style="background-color:#f2f2f2; font-weight:bold;">
                <td colspan="3" align="right">Total</td>
                <td>₹{total:,.0f}</td>
            </tr>
        </tfoot>
    </table>
    <br><p>Regards,<br>Automated Expense Scheduler</p>
    </body></html>
    """

# ── Send Email ───────────────────────────────────────────────────────────────
def send_email(html_body, month_name, total):
    sender   = os.environ["EMAIL_SENDER"]
    receiver = os.environ["EMAIL_RECEIVER"]
    password = os.environ["PASSWORD_API_KEY"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 Monthly Expense Report – {month_name} | Total: ₹{total:,.0f}"
    msg["From"]    = sender
    msg["To"]      = receiver

    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.starttls()
        s.login(sender, password)
        s.sendmail(sender, receiver, msg.as_string())

    print(f"✅ Expense report sent for {month_name}. Total: ₹{total:,.0f}")

# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    html = build_html(filtered_df, total, month_name)
    send_email(html, month_name, total)
    print(f"Total expenses for {month_name}: ₹{total:,.0f}")
