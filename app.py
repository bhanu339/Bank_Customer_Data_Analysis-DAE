import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Bank Customer Analytics", page_icon="🏦", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.8rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background: #f4f7fb; padding: 16px; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

st.title("🏦 Bank Customer Data Analysis System")
st.caption("Explore, clean, filter, and visualize bank customer data with Pandas.")

@st.cache_data
def load_demo():
    rng = np.random.default_rng(42)
    n = 500
    countries = ["India", "United Kingdom", "Germany", "France", "Spain", "United States"]
    types = ["Savings", "Current", "Salary", "Fixed Deposit"]
    genders = ["Female", "Male", "Other"]
    df = pd.DataFrame({
        "CustomerID": [f"C{i:04d}" for i in range(1, n + 1)],
        "Age": rng.integers(18, 81, n),
        "Gender": rng.choice(genders, n, p=[0.47, 0.49, 0.04]),
        "Country": rng.choice(countries, n),
        "AccountType": rng.choice(types, n, p=[0.45, 0.2, 0.25, 0.1]),
        "AccountBalance": np.round(rng.gamma(3.0, 1800, n), 2),
        "TransactionAmount": np.round(rng.gamma(2.0, 450, n), 2),
        "CreditScore": rng.integers(300, 851, n),
        "LoanStatus": rng.choice(["No Loan", "Approved", "Pending", "Rejected"], n, p=[0.48, 0.25, 0.12, 0.15]),
        "TenureYears": rng.integers(0, 31, n)
    })
    return df

with st.sidebar:
    st.header("Data source")
    upload = st.file_uploader("Upload a customer CSV", type=["csv"])
    st.info("No dataset yet? The app uses synthetic demo records. Replace these with your approved project dataset before reporting real findings.")
    st.header("Filters")

if upload is not None:
    try:
        raw = pd.read_csv(upload)
        source_label = f"Uploaded file: {upload.name}"
    except Exception as e:
        st.error(f"Could not read this CSV: {e}")
        st.stop()
else:
    raw = load_demo()
    source_label = "Synthetic demonstration dataset"

st.caption(source_label)
df = raw.copy()

with st.sidebar:
    if "Country" in df.columns:
        opts = sorted(df["Country"].dropna().astype(str).unique())
        selected_countries = st.multiselect("Country", opts, default=opts)
        df = df[df["Country"].astype(str).isin(selected_countries)]
    if "AccountType" in df.columns:
        opts = sorted(df["AccountType"].dropna().astype(str).unique())
        selected_types = st.multiselect("Account type", opts, default=opts)
        df = df[df["AccountType"].astype(str).isin(selected_types)]
    if "Gender" in df.columns:
        opts = sorted(df["Gender"].dropna().astype(str).unique())
        selected_genders = st.multiselect("Gender", opts, default=opts)
        df = df[df["Gender"].astype(str).isin(selected_genders)]
    if "Age" in df.columns and pd.api.types.is_numeric_dtype(df["Age"]) and not df["Age"].dropna().empty:
        lo, hi = int(df["Age"].min()), int(df["Age"].max())
        age_range = st.slider("Age range", lo, hi, (lo, hi))
        df = df[df["Age"].between(*age_range)]

tabs = st.tabs(["Overview", "Customer data", "Data quality", "Visualizations", "About"])

with tabs[0]:
    st.subheader("Overview")
    a, b, c, d = st.columns(4)
    a.metric("Customer records", f"{len(df):,}")
    b.metric("Columns", f"{df.shape[1]:,}")
    b_numeric = df.select_dtypes(include="number")
    if "AccountBalance" in df.columns and pd.api.types.is_numeric_dtype(df["AccountBalance"]):
        c.metric("Average balance", f"{df['AccountBalance'].mean():,.2f}" if df["AccountBalance"].notna().any() else "N/A")
    else:
        c.metric("Numeric columns", f"{b_numeric.shape[1]:,}")
    d.metric("Missing cells", f"{int(df.isna().sum().sum()):,}")
    left, right = st.columns(2)
    if "AccountType" in df.columns:
        counts = df["AccountType"].fillna("Missing").astype(str).value_counts().rename_axis("Account type").reset_index(name="Customers")
        left.plotly_chart(px.bar(counts, x="Account type", y="Customers", title="Customers by account type"), use_container_width=True)
    if "Country" in df.columns:
        counts = df["Country"].fillna("Missing").astype(str).value_counts().rename_axis("Country").reset_index(name="Customers")
        right.plotly_chart(px.pie(counts, names="Country", values="Customers", title="Customer distribution by country"), use_container_width=True)
    st.markdown("#### Descriptive statistics")
    st.dataframe(df.describe(include="all").transpose(), use_container_width=True)

with tabs[1]:
    st.subheader("Customer records")
    st.write(f"Showing **{len(df):,}** filtered records.")
    st.dataframe(df, use_container_width=True, height=440)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered data (CSV)", csv_bytes, "filtered_bank_customers.csv", "text/csv")
    search = st.text_input("Search within displayed records", placeholder="Enter a name, ID, country, or value")
    if search:
        mask = df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        st.dataframe(df[mask], use_container_width=True)

with tabs[2]:
    st.subheader("Data quality and cleaning")
    q1, q2, q3 = st.columns(3)
    q1.metric("Rows", f"{len(raw):,}")
    q2.metric("Duplicate rows", f"{int(raw.duplicated().sum()):,}")
    q3.metric("Missing cells", f"{int(raw.isna().sum().sum()):,}")
    quality = pd.DataFrame({
        "Column": raw.columns,
        "Data type": [str(t) for t in raw.dtypes],
        "Missing values": raw.isna().sum().values,
        "Missing (%)": (raw.isna().mean().values * 100).round(2),
        "Unique values": raw.nunique(dropna=True).values
    })
    st.dataframe(quality, use_container_width=True)
    st.markdown("#### Create a cleaned copy")
    fill_missing = st.checkbox("Fill missing numeric values with each column's median")
    remove_duplicates = st.checkbox("Remove duplicate rows", value=True)
    cleaned = raw.copy()
    if remove_duplicates:
        cleaned = cleaned.drop_duplicates()
    if fill_missing:
        for col in cleaned.select_dtypes(include="number").columns:
            if cleaned[col].isna().any():
                cleaned[col] = cleaned[col].fillna(cleaned[col].median())
    st.success(f"Cleaned copy: {len(cleaned):,} rows and {cleaned.isna().sum().sum():,} missing cells remain.")
    st.download_button("Download cleaned dataset", cleaned.to_csv(index=False).encode("utf-8"), "cleaned_bank_customers.csv", "text/csv")

with tabs[3]:
    st.subheader("Explore relationships")
    numeric_cols = list(df.select_dtypes(include="number").columns)
    categorical_cols = list(df.select_dtypes(exclude="number").columns)
    if numeric_cols:
        xcol = st.selectbox("Numeric variable for distribution", numeric_cols)
        st.plotly_chart(px.histogram(df, x=xcol, title=f"Distribution of {xcol}", marginal="box"), use_container_width=True)
    if len(numeric_cols) >= 2:
        x, y = st.columns(2)
        xcol = x.selectbox("X-axis", numeric_cols, index=0, key="scatterx")
        ycol = y.selectbox("Y-axis", numeric_cols, index=1, key="scattery")
        color_col = st.selectbox("Color by (optional)", ["None"] + categorical_cols, key="scattercolor")
        kwargs = {} if color_col == "None" else {"color": color_col}
        st.plotly_chart(px.scatter(df, x=xcol, y=ycol, title=f"{ycol} vs {xcol}", **kwargs), use_container_width=True)
    if categorical_cols:
        cat = st.selectbox("Category breakdown", categorical_cols)
        counts = df[cat].fillna("Missing").astype(str).value_counts().rename_axis(cat).reset_index(name="Count")
        st.plotly_chart(px.bar(counts, x=cat, y="Count", title=f"Records by {cat}"), use_container_width=True)
    if len(numeric_cols) >= 2:
        st.markdown("#### Numeric correlation matrix")
        st.plotly_chart(px.imshow(df[numeric_cols].corr(numeric_only=True), text_auto=".2f", aspect="auto", title="Correlation matrix"), use_container_width=True)

with tabs[4]:
    st.subheader("About this project")
    st.write("This is a local analytics dashboard built with Python, Pandas, NumPy, Streamlit, and Plotly.")
    st.write("It supports CSV loading, filtering, descriptive statistics, missing-value and duplicate checks, visual exploration, and CSV downloads.")
    st.warning("Demo values are synthetic and must not be presented as actual bank findings. Do not upload real customer personal or financial data unless you are authorized and the environment is approved for it.")
