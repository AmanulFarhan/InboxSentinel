import pandas as pd

df = pd.read_csv("job_portal_emails.csv")

output_path = "../datasets/raw/job_portal_emails.xlsx"

df.to_excel(
    output_path,
    index=False
)
print("Done")