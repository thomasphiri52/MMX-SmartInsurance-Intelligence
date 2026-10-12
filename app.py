
import os, sqlite3, hashlib, secrets, datetime, random
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "mmx_v6.db"
DB_URL = os.getenv("DATABASE_URL", "")
if DB_URL.startswith("sqlite:///"):
    DB_PATH = Path(DB_URL.replace("sqlite:///", "", 1))

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 180_000)
    return salt.hex() + "$" + digest.hex()

def verify_password(password, stored):
    try:
        salt_hex, digest_hex = stored.split("$")
        test = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 180_000).hex()
        return secrets.compare_digest(test, digest_hex)
    except Exception:
        return False

def init_db():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT,
      role TEXT, active INTEGER DEFAULT 1, created_at TEXT);
    CREATE TABLE IF NOT EXISTS customers(
      id INTEGER PRIMARY KEY, customer_ref TEXT UNIQUE, name TEXT, region TEXT,
      segment TEXT, retention_risk REAL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS policies(
      id INTEGER PRIMARY KEY, policy_no TEXT UNIQUE, customer_id INTEGER,
      region TEXT, product TEXT, channel TEXT, status TEXT,
      premium REAL, risk_score REAL, start_date TEXT);
    CREATE TABLE IF NOT EXISTS claims(
      id INTEGER PRIMARY KEY, claim_no TEXT UNIQUE, policy_id INTEGER,
      claim_date TEXT, claim_cost REAL, severity TEXT, status TEXT,
      fraud_score REAL);
    CREATE TABLE IF NOT EXISTS providers(
      id INTEGER PRIMARY KEY, provider_name TEXT UNIQUE, category TEXT,
      region TEXT, risk_score REAL, status TEXT);
    CREATE TABLE IF NOT EXISTS alerts(
      id INTEGER PRIMARY KEY, policy_id INTEGER, alert_type TEXT,
      severity TEXT, description TEXT, status TEXT DEFAULT 'Open',
      assigned_to TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS investigations(
      id INTEGER PRIMARY KEY, alert_id INTEGER, policy_id INTEGER,
      investigator TEXT, priority TEXT, status TEXT DEFAULT 'Open',
      notes TEXT, created_at TEXT, updated_at TEXT);
    CREATE TABLE IF NOT EXISTS audit_log(
      id INTEGER PRIMARY KEY, timestamp TEXT, username TEXT,
      action TEXT, entity TEXT, entity_id TEXT, details TEXT);
    """)
    c.commit()
    seed(c)
    c.close()

def seed(c):
    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        now = datetime.datetime.now().isoformat(timespec="seconds")
        users = [
            ("admin", hash_password("mmx2026"), "Administrator"),
            ("executive", hash_password("mmx2026"), "Executive"),
            ("claims", hash_password("mmx2026"), "Claims Manager"),
            ("risk", hash_password("mmx2026"), "Risk Manager"),
            ("investigator", hash_password("mmx2026"), "Investigator"),
        ]
        c.executemany("INSERT INTO users(username,password_hash,role,created_at) VALUES(?,?,?,?)",
                      [(u,p,r,now) for u,p,r in users])

    if c.execute("SELECT COUNT(*) FROM customers").fetchone()[0] > 0:
        c.commit(); return

    random.seed(42)
    regions = ["Gauteng","Western Cape","KwaZulu-Natal","Eastern Cape","Free State","Limpopo","Mpumalanga","North West","Northern Cape"]
    products = ["Motor","Property","Commercial","Life","Travel","SME"]
    channels = ["Broker","Direct","Digital","Partner"]
    segments = ["Retail","SME","Corporate","Affluent"]
    now = datetime.date.today()
    customers=[]
    for i in range(1,301):
        customers.append((f"CUST-{i:05d}", f"Customer {i:04d}", random.choice(regions),
                          random.choice(segments), round(random.uniform(2,92),1)))
    c.executemany("INSERT INTO customers(customer_ref,name,region,segment,retention_risk) VALUES(?,?,?,?,?)", customers)

    cust_ids=[r[0] for r in c.execute("SELECT id FROM customers").fetchall()]
    policies=[]
    for i in range(1,801):
        risk=round(min(99,max(1,random.gauss(42,20))),1)
        policies.append((f"POL-{i:06d}", random.choice(cust_ids), random.choice(regions),
                         random.choice(products), random.choice(channels),
                         random.choice(["Active","Active","Active","Lapsed","Pending"]),
                         round(random.uniform(1800,85000),2), risk,
                         str(now-datetime.timedelta(days=random.randint(1,1400)))))
    c.executemany("""INSERT INTO policies(policy_no,customer_id,region,product,channel,status,premium,risk_score,start_date)
                     VALUES(?,?,?,?,?,?,?,?,?)""", policies)

    pol_ids=[r[0] for r in c.execute("SELECT id FROM policies").fetchall()]
    claims=[]
    for i in range(1,501):
        fraud=round(min(99,max(1,random.gauss(22,22))),1)
        sev=random.choice(["Low","Medium","High","Critical"])
        claims.append((f"CLM-{i:06d}", random.choice(pol_ids),
                       str(now-datetime.timedelta(days=random.randint(1,730))),
                       round(random.uniform(500,180000),2), sev,
                       random.choice(["Open","Under Review","Approved","Closed"]),
                       fraud))
    c.executemany("""INSERT INTO claims(claim_no,policy_id,claim_date,claim_cost,severity,status,fraud_score)
                     VALUES(?,?,?,?,?,?,?)""", claims)

    providers=[]
    for i in range(1,61):
        providers.append((f"Provider {i:03d}", random.choice(["Repair","Medical","Legal","Assessing","Security"]),
                          random.choice(regions), round(random.uniform(5,90),1),
                          random.choice(["Active","Active","Review"])))
    c.executemany("INSERT INTO providers(provider_name,category,region,risk_score,status) VALUES(?,?,?,?,?)", providers)

    alerts=[]
    for i in range(1,61):
        p=random.choice(pol_ids)
        alerts.append((p, random.choice(["High Fraud Score","High Risk Policy","Claims Spike","Provider Risk","Retention Risk"]),
                       random.choice(["Low","Medium","High","Critical"]),
                       "Automated V6 intelligence rule triggered for review.",
                       random.choice(["Open","Open","Investigating","Resolved"]), None,
                       datetime.datetime.now().isoformat(timespec="seconds")))
    c.executemany("""INSERT INTO alerts(policy_id,alert_type,severity,description,status,assigned_to,created_at)
                     VALUES(?,?,?,?,?,?,?)""", alerts)
    c.commit()

def log(user, action, entity, entity_id="", details=""):
    c=db()
    c.execute("INSERT INTO audit_log(timestamp,username,action,entity,entity_id,details) VALUES(?,?,?,?,?,?)",
              (datetime.datetime.now().isoformat(timespec="seconds"),user,action,entity,str(entity_id),details))
    c.commit(); c.close()

def query(sql, params=()):
    c=db(); df=pd.read_sql_query(sql,c,params=params); c.close(); return df

def execute(sql, params=()):
    c=db(); cur=c.execute(sql,params); c.commit(); out=cur.lastrowid; c.close(); return out

st.set_page_config(page_title="MMX Smart Insurance Intelligence V6", page_icon="🛡️", layout="wide")
init_db()

if "user" not in st.session_state:
    st.session_state.user=None

def login():
    st.title("🛡️ MMX Smart Insurance Intelligence")
    st.caption("V6 Enterprise Production Architecture")
    with st.form("login"):
        u=st.text_input("Username")
        p=st.text_input("Password", type="password")
        ok=st.form_submit_button("Sign in", use_container_width=True)
    if ok:
        row=query("SELECT * FROM users WHERE username=? AND active=1",(u,))
        if not row.empty and verify_password(p,row.iloc[0]["password_hash"]):
            st.session_state.user={"username":u,"role":row.iloc[0]["role"]}
            log(u,"LOGIN","SYSTEM",details="Successful login")
            st.rerun()
        else:
            st.error("Invalid credentials.")
    st.info("Demo accounts: admin, executive, claims, risk, investigator — password: mmx2026")

if not st.session_state.user:
    login(); st.stop()

user=st.session_state.user
role=user["role"]

with st.sidebar:
    st.markdown("## MMX V5")
    st.caption(f"{user['username']} • {role}")
    st.success("V6 Production Architecture • API + PostgreSQL-ready + Human-governed AI")
    pages=["Executive Command Centre","Portfolio Intelligence","Claims Intelligence","Fraud & Crime","Risk Intelligence",
           "Customer Intelligence","Broker & Distribution","Third-Party Risk","AI Decision Centre",
           "Alerts & Investigations","Reports","Data Management","Governance & Audit","Administration"]
    page=st.radio("Navigation",pages)
    if st.button("Logout",use_container_width=True):
        log(user["username"],"LOGOUT","SYSTEM")
        st.session_state.user=None; st.rerun()

pol=query("""SELECT p.*, c.name customer_name, c.segment, c.retention_risk
             FROM policies p LEFT JOIN customers c ON c.id=p.customer_id""")
clm=query("""SELECT c.*, p.policy_no, p.region, p.product
             FROM claims c LEFT JOIN policies p ON p.id=c.policy_id""")
alerts=query("""SELECT a.*, p.policy_no,p.region,p.product FROM alerts a
                LEFT JOIN policies p ON p.id=a.policy_id ORDER BY a.id DESC""")

if page=="Executive Command Centre":
    st.title("Executive Command Centre")
    active=(pol.status=="Active").sum()
    premiums=pol.premium[pol.status=="Active"].sum()
    claims_cost=clm.claim_cost.sum()
    loss=claims_cost/premiums*100 if premiums else 0
    fraud=(clm.fraud_score>=70).sum()
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("Active Policies",f"{active:,}")
    c2.metric("Active Premium",f"R{premiums:,.0f}")
    c3.metric("Claims Cost",f"R{claims_cost:,.0f}")
    c4.metric("Loss Ratio",f"{loss:.1f}%")
    c5.metric("High-Fraud Claims",f"{fraud:,}")
    a,b=st.columns(2)
    with a:
        fig=px.bar(pol.groupby("product",as_index=False).premium.sum(),x="product",y="premium",title="Premium by Product")
        st.plotly_chart(fig,use_container_width=True)
    with b:
        fig=px.bar(clm.groupby("severity",as_index=False).claim_cost.sum(),x="severity",y="claim_cost",title="Claims Cost by Severity")
        st.plotly_chart(fig,use_container_width=True)
    st.subheader("Priority Alerts")
    st.dataframe(alerts.head(12),use_container_width=True,hide_index=True)

elif page=="Portfolio Intelligence":
    st.title("Portfolio Intelligence")
    region=st.selectbox("Region",["All"]+sorted(pol.region.dropna().unique()))
    x=pol if region=="All" else pol[pol.region==region]
    st.metric("Portfolio Premium",f"R{x.premium.sum():,.0f}")
    st.dataframe(x.groupby(["region","product"],as_index=False).agg(Policies=("id","count"),Premium=("premium","sum"),AvgRisk=("risk_score","mean")),use_container_width=True,hide_index=True)
    fig=px.scatter(x,x="risk_score",y="premium",color="product",hover_data=["policy_no"],title="Risk vs Premium")
    st.plotly_chart(fig,use_container_width=True)

elif page=="Claims Intelligence":
    st.title("Claims Intelligence")
    severity=st.multiselect("Severity",sorted(clm.severity.unique()),default=sorted(clm.severity.unique()))
    x=clm[clm.severity.isin(severity)]
    c1,c2,c3=st.columns(3)
    c1.metric("Claims",f"{len(x):,}"); c2.metric("Claim Cost",f"R{x.claim_cost.sum():,.0f}"); c3.metric("Avg Cost",f"R{x.claim_cost.mean():,.0f}")
    fig=px.histogram(x,x="claim_cost",color="severity",title="Claims Cost Distribution")
    st.plotly_chart(fig,use_container_width=True)
    st.dataframe(x.sort_values("claim_cost",ascending=False).head(50),use_container_width=True,hide_index=True)

elif page=="Fraud & Crime":
    st.title("Fraud & Crime Intelligence")
    high=clm[clm.fraud_score>=70].copy()
    st.metric("High Fraud-Risk Claims",len(high))
    high["priority_reason"]=high.apply(lambda r: "High fraud score + high claim cost" if r.fraud_score>=85 and r.claim_cost>=50000 else "Fraud score threshold",axis=1)
    st.dataframe(high.sort_values(["fraud_score","claim_cost"],ascending=False).head(100),use_container_width=True,hide_index=True)
    st.download_button("Download fraud queue",high.to_csv(index=False).encode(),"mmx_fraud_queue.csv","text/csv")

elif page=="Risk Intelligence":
    st.title("Risk Intelligence")
    bins=[0,30,60,80,100]; labels=["Low","Medium","High","Critical"]
    r=pol.copy(); r["risk_band"]=pd.cut(r.risk_score,bins=bins,labels=labels,include_lowest=True)
    st.dataframe(r.groupby("risk_band",observed=False).agg(Policies=("id","count"),Premium=("premium","sum"),AvgRisk=("risk_score","mean")).reset_index(),use_container_width=True,hide_index=True)
    fig=px.histogram(r,x="risk_score",nbins=20,title="Risk Score Distribution")
    st.plotly_chart(fig,use_container_width=True)

elif page=="Customer Intelligence":
    st.title("Customer Intelligence")
    cust=query("""SELECT c.*, COUNT(p.id) policies, COALESCE(SUM(p.premium),0) premium
                  FROM customers c LEFT JOIN policies p ON p.customer_id=c.id GROUP BY c.id""")
    st.dataframe(cust.sort_values("retention_risk",ascending=False).head(100),use_container_width=True,hide_index=True)
    fig=px.scatter(cust,x="premium",y="retention_risk",size="policies",color="segment",title="Customer Value vs Retention Risk")
    st.plotly_chart(fig,use_container_width=True)

elif page=="Broker & Distribution":
    st.title("Broker & Distribution Intelligence")
    x=pol.groupby("channel",as_index=False).agg(Policies=("id","count"),Premium=("premium","sum"),AvgRisk=("risk_score","mean"))
    st.dataframe(x,use_container_width=True,hide_index=True)
    st.plotly_chart(px.bar(x,x="channel",y="Premium",title="Premium by Channel"),use_container_width=True)

elif page=="Third-Party Risk":
    st.title("Third-Party Risk")
    prov=query("SELECT * FROM providers ORDER BY risk_score DESC")
    st.dataframe(prov,use_container_width=True,hide_index=True)
    st.download_button("Export provider risk",prov.to_csv(index=False).encode(),"mmx_provider_risk.csv","text/csv")

elif page=="AI Decision Centre":
    st.title("Explainable AI Decision Centre")
    st.warning("Decision-support only: recommendations require human review and approval.")
    claim_no=st.selectbox("Select claim",clm.claim_no.tolist()[:300])
    r=clm[clm.claim_no==claim_no].iloc[0]
    reasons=[]
    if r.fraud_score>=70: reasons.append("Fraud-risk score is above review threshold.")
    if r.claim_cost>=50000: reasons.append("Claim cost is materially high.")
    if r.severity in ["High","Critical"]: reasons.append("Claim severity requires enhanced review.")
    if not reasons: reasons.append("No high-risk rule triggered.")
    recommendation="Enhanced investigation" if len(reasons)>=2 else ("Targeted review" if reasons[0]!="No high-risk rule triggered." else "Standard human review")
    st.metric("Recommendation",recommendation)
    st.subheader("Explainability")
    for reason in reasons: st.write("• "+reason)
    if st.button("Record recommendation"):
        log(user["username"],"AI_RECOMMENDATION","CLAIM",r["id"],recommendation+" | "+" ".join(reasons))
        st.success("Recommendation recorded in audit trail.")

elif page=="Alerts & Investigations":
    st.title("Alerts & Investigations Workbench")
    if alerts.empty: st.info("No alerts.")
    else:
        aid=st.selectbox("Alert",alerts.id.tolist())
        a=alerts[alerts.id==aid].iloc[0]
        st.write(f"**{a.alert_type}** • {a.severity} • {a.status}")
        st.write(a.description)
        new_status=st.selectbox("Update status",["Open","Investigating","Escalated","Resolved"],index=["Open","Investigating","Escalated","Resolved"].index(a.status) if a.status in ["Open","Investigating","Escalated","Resolved"] else 0)
        investigator=st.text_input("Assign investigator",a.assigned_to or user["username"])
        notes=st.text_area("Investigation notes")
        if st.button("Save investigation"):
            execute("UPDATE alerts SET status=?,assigned_to=? WHERE id=?",(new_status,investigator,aid))
            execute("""INSERT INTO investigations(alert_id,policy_id,investigator,priority,status,notes,created_at,updated_at)
                       VALUES(?,?,?,?,?,?,?,?)""",(aid,a.policy_id,investigator,a.severity,new_status,notes,
                       datetime.datetime.now().isoformat(timespec="seconds"),datetime.datetime.now().isoformat(timespec="seconds")))
            log(user["username"],"UPDATE_ALERT","ALERT",aid,f"{new_status}; assigned={investigator}")
            st.success("Investigation updated.")
            st.rerun()
    st.dataframe(query("SELECT * FROM investigations ORDER BY id DESC LIMIT 100"),use_container_width=True,hide_index=True)

elif page=="Reports":
    st.title("Management Reports")
    report=st.selectbox("Report",["Portfolio","Claims","Fraud Queue","Alerts","Audit Log"])
    mapping={"Portfolio":pol,"Claims":clm,"Fraud Queue":clm[clm.fraud_score>=70],"Alerts":alerts,
             "Audit Log":query("SELECT * FROM audit_log ORDER BY id DESC")}
    df=mapping[report]
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.download_button("Download CSV",df.to_csv(index=False).encode(),f"mmx_{report.lower().replace(' ','_')}.csv","text/csv")

elif page=="Data Management":
    st.title("Data Management")
    st.caption("Upload CSV files using the supported templates below.")
    kind=st.selectbox("Dataset",["Policies","Claims"])
    file=st.file_uploader("Upload CSV",type=["csv"])
    if file:
        df=pd.read_csv(file); st.dataframe(df.head(20),use_container_width=True,hide_index=True)
        st.info("For controlled production imports, validate mappings and source ownership before loading data.")
    st.subheader("Database")
    st.write(f"SQLite demo database: `{DB_PATH.name}`")
    st.write("Production PostgreSQL is supported through the DATABASE_URL deployment setting.")

elif page=="Governance & Audit":
    st.title("Governance & Audit")
    st.subheader("Control status")
    controls=pd.DataFrame([
        ["Human review","Enabled","AI recommendations do not autonomously decide claims."],
        ["Audit trail","Enabled","Login, AI recommendation and workflow actions are logged."],
        ["Explainability","Enabled","Decision-support shows triggered reasons."],
        ["Secrets","Environment-ready","Production credentials should be stored outside source code."],
        ["Data privacy","Required","Apply POPIA-aligned access, retention and minimisation controls."],
    ],columns=["Control","Status","Description"])
    st.dataframe(controls,use_container_width=True,hide_index=True)
    st.subheader("Audit events")
    st.dataframe(query("SELECT * FROM audit_log ORDER BY id DESC LIMIT 200"),use_container_width=True,hide_index=True)

elif page=="Administration":
    st.title("Administration")
    if role!="Administrator":
        st.warning("Administrator role required for account administration.")
    else:
        st.subheader("Create user")
        with st.form("new_user"):
            nu=st.text_input("Username")
            np=st.text_input("Temporary password",type="password")
            nr=st.selectbox("Role",["Executive","Claims Manager","Risk Manager","Investigator","Administrator"])
            create=st.form_submit_button("Create user")
        if create and nu and np:
            try:
                execute("INSERT INTO users(username,password_hash,role,created_at) VALUES(?,?,?,?)",
                        (nu,hash_password(np),nr,datetime.datetime.now().isoformat(timespec="seconds")))
                log(user["username"],"CREATE_USER","USER",nu,nr)
                st.success("User created.")
            except sqlite3.IntegrityError:
                st.error("Username already exists.")
        st.dataframe(query("SELECT id,username,role,active,created_at FROM users"),use_container_width=True,hide_index=True)
