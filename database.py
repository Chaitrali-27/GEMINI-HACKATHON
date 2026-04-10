"""
database.py — SentinelIQ Database
Run ONCE: python database.py
"""

import sqlite3, hashlib, os, random, string
from datetime import datetime, timedelta

DB_PATH = "sentineliq.db"

INDIA_DATA = {
    "Andhra Pradesh": ["Alluri Sitharama Raju","Anakapalli","Ananthapuramu","Annamayya","Bapatla","Chittoor","Dr. B.R. Ambedkar Konaseema","East Godavari","Eluru","Guntur","Kadapa","Kakinada","Krishna","Kurnool","Nandyal","Nellore","NTR","Palnadu","Parvathipuram Manyam","Prakasam","Srikakulam","Tirupati","Visakhapatnam","Vizianagaram","West Godavari"],
    "Arunachal Pradesh": ["Anjaw","Changlang","Dibang Valley","East Kameng","East Siang","Itanagar Capital Complex","Kamle","Kra Daadi","Kurung Kumey","Lepa Rada","Lohit","Longding","Lower Dibang Valley","Lower Siang","Lower Subansiri","Namsai","Pakke Kessang","Papum Pare","Shi Yomi","Siang","Tawang","Tirap","Upper Siang","Upper Subansiri","West Kameng","West Siang"],
    "Assam": ["Bajali","Baksa","Barpeta","Biswanath","Bongaigaon","Cachar","Charaideo","Chirang","Darrang","Dhemaji","Dhubri","Dibrugarh","Dima Hasao","Goalpara","Golaghat","Hailakandi","Hojai","Jorhat","Kamrup","Kamrup Metropolitan","Karbi Anglong","Karimganj","Kokrajhar","Lakhimpur","Majuli","Morigaon","Nagaon","Nalbari","Sivasagar","Sonitpur","South Salmara-Mankachar","Tinsukia","Udalguri","West Karbi Anglong"],
    "Bihar": ["Araria","Arwal","Aurangabad","Banka","Begusarai","Bhagalpur","Bhojpur","Buxar","Darbhanga","East Champaran","Gaya","Gopalganj","Jamui","Jehanabad","Kaimur","Katihar","Khagaria","Kishanganj","Lakhisarai","Madhepura","Madhubani","Munger","Muzaffarpur","Nalanda","Nawada","Patna","Purnia","Rohtas","Saharsa","Samastipur","Saran","Sheikhpura","Sheohar","Sitamarhi","Siwan","Supaul","Vaishali","West Champaran"],
    "Chhattisgarh": ["Balod","Baloda Bazar","Balrampur","Bastar","Bemetara","Bijapur","Bilaspur","Dantewada","Dhamtari","Durg","Gariaband","Gaurela Pendra Marwahi","Janjgir Champa","Jashpur","Kabirdham","Kanker","Khairagarh","Kondagaon","Korba","Koriya","Mahasamund","Manendragarh","Mohla Manpur","Mungeli","Narayanpur","Raigarh","Raipur","Rajnandgaon","Sakti","Sarangarh Bilaigarh","Sukma","Surajpur","Surguja"],
    "Goa": ["North Goa","South Goa"],
    "Gujarat": ["Ahmedabad","Amreli","Anand","Aravalli","Banaskantha","Bharuch","Bhavnagar","Botad","Chhota Udaipur","Dahod","Dang","Devbhoomi Dwarka","Gandhinagar","Gir Somnath","Jamnagar","Junagadh","Kheda","Kutch","Mahisagar","Mehsana","Morbi","Narmada","Navsari","Panchmahal","Patan","Porbandar","Rajkot","Sabarkantha","Surat","Surendranagar","Tapi","Vadodara","Valsad"],
    "Haryana": ["Ambala","Bhiwani","Charkhi Dadri","Faridabad","Fatehabad","Gurugram","Hisar","Jhajjar","Jind","Kaithal","Karnal","Kurukshetra","Mahendragarh","Nuh","Palwal","Panchkula","Panipat","Rewari","Rohtak","Sirsa","Sonipat","Yamunanagar"],
    "Himachal Pradesh": ["Bilaspur","Chamba","Hamirpur","Kangra","Kinnaur","Kullu","Lahaul Spiti","Mandi","Shimla","Sirmaur","Solan","Una"],
    "Jharkhand": ["Bokaro","Chatra","Deoghar","Dhanbad","Dumka","East Singhbhum","Garhwa","Giridih","Godda","Gumla","Hazaribagh","Jamtara","Khunti","Koderma","Latehar","Lohardaga","Pakur","Palamu","Ramgarh","Ranchi","Sahebganj","Seraikela Kharsawan","Simdega","West Singhbhum"],
    "Karnataka": ["Bagalkot","Ballari","Belagavi","Bengaluru Rural","Bengaluru Urban","Bidar","Chamarajanagar","Chikkaballapur","Chikkamagaluru","Chitradurga","Dakshina Kannada","Davangere","Dharwad","Gadag","Hassan","Haveri","Kalaburagi","Kodagu","Kolar","Koppal","Mandya","Mysuru","Raichur","Ramanagara","Shivamogga","Tumakuru","Udupi","Uttara Kannada","Vijayanagara","Vijayapura","Yadgir"],
    "Kerala": ["Alappuzha","Ernakulam","Idukki","Kannur","Kasaragod","Kollam","Kottayam","Kozhikode","Malappuram","Palakkad","Pathanamthitta","Thiruvananthapuram","Thrissur","Wayanad"],
    "Madhya Pradesh": ["Agar Malwa","Alirajpur","Anuppur","Ashoknagar","Balaghat","Barwani","Betul","Bhind","Bhopal","Burhanpur","Chhatarpur","Chhindwara","Damoh","Datia","Dewas","Dhar","Dindori","Guna","Gwalior","Harda","Hoshangabad","Indore","Jabalpur","Jhabua","Katni","Khandwa","Khargone","Mandla","Mandsaur","Morena","Narsinghpur","Neemuch","Niwari","Panna","Raisen","Rajgarh","Ratlam","Rewa","Sagar","Satna","Sehore","Seoni","Shahdol","Shajapur","Sheopur","Shivpuri","Sidhi","Singrauli","Tikamgarh","Ujjain","Umaria","Vidisha"],
    "Maharashtra": ["Ahmednagar","Akola","Amravati","Aurangabad","Beed","Bhandara","Buldhana","Chandrapur","Dhule","Gadchiroli","Gondia","Hingoli","Jalgaon","Jalna","Kolhapur","Latur","Mumbai City","Mumbai Suburban","Nagpur","Nanded","Nandurbar","Nashik","Osmanabad","Palghar","Parbhani","Pune","Raigad","Ratnagiri","Sangli","Satara","Sindhudurg","Solapur","Thane","Wardha","Washim","Yavatmal"],
    "Manipur": ["Bishnupur","Chandel","Churachandpur","Imphal East","Imphal West","Jiribam","Kakching","Kamjong","Kangpokpi","Noney","Pherzawl","Senapati","Tamenglong","Tengnoupal","Thoubal","Ukhrul"],
    "Meghalaya": ["East Garo Hills","East Jaintia Hills","East Khasi Hills","Eastern West Khasi Hills","North Garo Hills","Ri Bhoi","South Garo Hills","South West Garo Hills","South West Khasi Hills","West Garo Hills","West Jaintia Hills","West Khasi Hills"],
    "Mizoram": ["Aizawl","Champhai","Hnahthial","Khawzawl","Kolasib","Lawngtlai","Lunglei","Mamit","Saitual","Serchhip","Siaha"],
    "Nagaland": ["Chumoukedima","Dimapur","Kiphire","Kohima","Longleng","Mokokchung","Mon","Niuland","Noklak","Peren","Phek","Shamator","Tseminyu","Tuensang","Wokha","Zunheboto"],
    "Odisha": ["Angul","Balangir","Balasore","Bargarh","Bhadrak","Boudh","Cuttack","Deogarh","Dhenkanal","Gajapati","Ganjam","Jagatsinghpur","Jajpur","Jharsuguda","Kalahandi","Kandhamal","Kendrapara","Kendujhar","Khordha","Koraput","Malkangiri","Mayurbhanj","Nabarangpur","Nayagarh","Nuapada","Puri","Rayagada","Sambalpur","Sonepur","Sundargarh"],
    "Punjab": ["Amritsar","Barnala","Bathinda","Faridkot","Fatehgarh Sahib","Fazilka","Ferozepur","Gurdaspur","Hoshiarpur","Jalandhar","Kapurthala","Ludhiana","Malerkotla","Mansa","Moga","Mohali","Muktsar","Pathankot","Patiala","Rupnagar","Sangrur","Shahid Bhagat Singh Nagar","Tarn Taran"],
    "Rajasthan": ["Ajmer","Alwar","Banswara","Baran","Barmer","Bharatpur","Bhilwara","Bikaner","Bundi","Chittorgarh","Churu","Dausa","Dholpur","Dungarpur","Ganganagar","Hanumangarh","Jaipur","Jaisalmer","Jalore","Jhalawar","Jhunjhunu","Jodhpur","Karauli","Kota","Nagaur","Pali","Pratapgarh","Rajsamand","Sawai Madhopur","Sikar","Sirohi","Tonk","Udaipur"],
    "Sikkim": ["East Sikkim","North Sikkim","Pakyong","Soreng","South Sikkim","West Sikkim"],
    "Tamil Nadu": ["Ariyalur","Chengalpattu","Chennai","Coimbatore","Cuddalore","Dharmapuri","Dindigul","Erode","Kallakurichi","Kancheepuram","Kanyakumari","Karur","Krishnagiri","Madurai","Mayiladuthurai","Nagapattinam","Namakkal","Nilgiris","Perambalur","Pudukkottai","Ramanathapuram","Ranipet","Salem","Sivaganga","Tenkasi","Thanjavur","Theni","Thoothukudi","Tiruchirappalli","Tirunelveli","Tirupattur","Tiruppur","Tiruvallur","Tiruvannamalai","Tiruvarur","Vellore","Viluppuram","Virudhunagar"],
    "Telangana": ["Adilabad","Bhadradri Kothagudem","Hanumakonda","Hyderabad","Jagtial","Jangaon","Jayashankar Bhupalpally","Jogulamba Gadwal","Kamareddy","Karimnagar","Khammam","Kumuram Bheem","Mahabubabad","Mahbubnagar","Mancherial","Medak","Medchal Malkajgiri","Mulugu","Nagarkurnool","Nalgonda","Narayanpet","Nirmal","Nizamabad","Peddapalli","Rajanna Sircilla","Rangareddy","Sangareddy","Siddipet","Suryapet","Vikarabad","Wanaparthy","Warangal","Yadadri Bhuvanagiri"],
    "Tripura": ["Dhalai","Gomati","Khowai","North Tripura","Sepahijala","South Tripura","Unakoti","West Tripura"],
    "Uttar Pradesh": ["Agra","Aligarh","Ambedkar Nagar","Amethi","Amroha","Auraiya","Ayodhya","Azamgarh","Baghpat","Bahraich","Ballia","Balrampur","Banda","Barabanki","Bareilly","Basti","Bhadohi","Bijnor","Budaun","Bulandshahr","Chandauli","Chitrakoot","Deoria","Etah","Etawah","Farrukhabad","Fatehpur","Firozabad","Gautam Buddha Nagar","Ghaziabad","Ghazipur","Gonda","Gorakhpur","Hamirpur","Hapur","Hardoi","Hathras","Jalaun","Jaunpur","Jhansi","Kannauj","Kanpur Dehat","Kanpur Nagar","Kasganj","Kaushambi","Kheri","Kushinagar","Lalitpur","Lucknow","Maharajganj","Mahoba","Mainpuri","Mathura","Mau","Meerut","Mirzapur","Moradabad","Muzaffarnagar","Pilibhit","Pratapgarh","Prayagraj","Raebareli","Rampur","Saharanpur","Sambhal","Sant Kabir Nagar","Shahjahanpur","Shamli","Shravasti","Siddharthnagar","Sitapur","Sonbhadra","Sultanpur","Unnao","Varanasi"],
    "Uttarakhand": ["Almora","Bageshwar","Chamoli","Champawat","Dehradun","Haridwar","Nainital","Pauri Garhwal","Pithoragarh","Rudraprayag","Tehri Garhwal","Udham Singh Nagar","Uttarkashi"],
    "West Bengal": ["Alipurduar","Bankura","Birbhum","Cooch Behar","Dakshin Dinajpur","Darjeeling","Hooghly","Howrah","Jalpaiguri","Jhargram","Kalimpong","Kolkata","Malda","Murshidabad","Nadia","North 24 Parganas","Paschim Bardhaman","Paschim Medinipur","Purba Bardhaman","Purba Medinipur","Purulia","South 24 Parganas","Uttar Dinajpur"],
    "Delhi": ["Central Delhi","East Delhi","New Delhi","North Delhi","North East Delhi","North West Delhi","Shahdara","South Delhi","South East Delhi","South West Delhi","West Delhi"],
    "Jammu & Kashmir": ["Anantnag","Bandipora","Baramulla","Budgam","Doda","Ganderbal","Jammu","Kathua","Kishtwar","Kulgam","Kupwara","Poonch","Pulwama","Rajouri","Ramban","Reasi","Samba","Shopian","Srinagar","Udhampur"],
    "Ladakh": ["Kargil","Leh"],
    "Chandigarh": ["Chandigarh"],
    "Puducherry": ["Karaikal","Mahe","Puducherry","Yanam"],
    "Andaman & Nicobar Islands": ["Nicobar","North and Middle Andaman","South Andaman"],
    "Dadra & Nagar Haveli and Daman & Diu": ["Dadra and Nagar Haveli","Daman","Diu"],
    "Lakshadweep": ["Lakshadweep"],
}

MACHINE_TYPES = [
    "CNC Milling Machine","Industrial Lathe","Hydraulic Press",
    "Conveyor Belt System","Compressor Unit","Pump Station",
    "Welding Robot","Injection Moulding Machine","Packaging Machine",
    "Industrial Boiler","Generator Unit","Grinding Machine",
    "Cutting Machine","Assembly Robot","Other"
]

SENSOR_RANGES = {
    "CNC Milling Machine":        {"Air temperature [K]":(295,305),"Process temperature [K]":(305,315),"Rotational speed [rpm]":(1400,1600),"Torque [Nm]":(35,55),"Tool wear [min]":(0,100),"Vibration Sensor [g]":(0.2,0.6),"Acoustic Emission [dB]":(60,75),"Current Draw [A]":(8,12)},
    "Industrial Lathe":           {"Air temperature [K]":(298,310),"Process temperature [K]":(310,325),"Rotational speed [rpm]":(1500,1800),"Torque [Nm]":(40,65),"Tool wear [min]":(50,180),"Vibration Sensor [g]":(0.5,0.9),"Acoustic Emission [dB]":(70,85),"Current Draw [A]":(10,15)},
    "Hydraulic Press":            {"Air temperature [K]":(300,315),"Process temperature [K]":(315,330),"Rotational speed [rpm]":(1200,1500),"Torque [Nm]":(50,80),"Tool wear [min]":(100,250),"Vibration Sensor [g]":(0.7,1.2),"Acoustic Emission [dB]":(75,95),"Current Draw [A]":(12,18)},
    "Conveyor Belt System":       {"Air temperature [K]":(293,303),"Process temperature [K]":(300,310),"Rotational speed [rpm]":(800,1200),"Torque [Nm]":(20,40),"Tool wear [min]":(0,80),"Vibration Sensor [g]":(0.1,0.4),"Acoustic Emission [dB]":(55,70),"Current Draw [A]":(6,10)},
    "Compressor Unit":            {"Air temperature [K]":(305,320),"Process temperature [K]":(320,340),"Rotational speed [rpm]":(2000,3000),"Torque [Nm]":(60,100),"Tool wear [min]":(0,60),"Vibration Sensor [g]":(0.3,0.8),"Acoustic Emission [dB]":(75,90),"Current Draw [A]":(15,25)},
    "Pump Station":               {"Air temperature [K]":(295,308),"Process temperature [K]":(308,320),"Rotational speed [rpm]":(1000,1500),"Torque [Nm]":(25,50),"Tool wear [min]":(0,70),"Vibration Sensor [g]":(0.2,0.5),"Acoustic Emission [dB]":(60,78),"Current Draw [A]":(7,13)},
    "Welding Robot":              {"Air temperature [K]":(310,330),"Process temperature [K]":(330,360),"Rotational speed [rpm]":(500,900),"Torque [Nm]":(80,150),"Tool wear [min]":(10,120),"Vibration Sensor [g]":(0.4,1.0),"Acoustic Emission [dB]":(80,100),"Current Draw [A]":(20,35)},
    "Injection Moulding Machine": {"Air temperature [K]":(308,325),"Process temperature [K]":(325,355),"Rotational speed [rpm]":(600,1000),"Torque [Nm]":(100,200),"Tool wear [min]":(20,150),"Vibration Sensor [g]":(0.3,0.7),"Acoustic Emission [dB]":(65,82),"Current Draw [A]":(18,30)},
    "Packaging Machine":          {"Air temperature [K]":(293,303),"Process temperature [K]":(300,312),"Rotational speed [rpm]":(1200,2000),"Torque [Nm]":(15,35),"Tool wear [min]":(0,90),"Vibration Sensor [g]":(0.1,0.4),"Acoustic Emission [dB]":(58,72),"Current Draw [A]":(5,9)},
    "Industrial Boiler":          {"Air temperature [K]":(320,360),"Process temperature [K]":(360,420),"Rotational speed [rpm]":(200,500),"Torque [Nm]":(150,300),"Tool wear [min]":(0,40),"Vibration Sensor [g]":(0.2,0.6),"Acoustic Emission [dB]":(70,88),"Current Draw [A]":(25,45)},
    "Generator Unit":             {"Air temperature [K]":(308,325),"Process temperature [K]":(320,340),"Rotational speed [rpm]":(1500,3000),"Torque [Nm]":(200,400),"Tool wear [min]":(0,50),"Vibration Sensor [g]":(0.3,0.9),"Acoustic Emission [dB]":(78,95),"Current Draw [A]":(30,60)},
    "Grinding Machine":           {"Air temperature [K]":(298,312),"Process temperature [K]":(312,328),"Rotational speed [rpm]":(2000,4000),"Torque [Nm]":(30,70),"Tool wear [min]":(10,200),"Vibration Sensor [g]":(0.4,1.1),"Acoustic Emission [dB]":(80,100),"Current Draw [A]":(10,18)},
    "Cutting Machine":            {"Air temperature [K]":(296,308),"Process temperature [K]":(308,322),"Rotational speed [rpm]":(1800,3500),"Torque [Nm]":(25,60),"Tool wear [min]":(5,180),"Vibration Sensor [g]":(0.3,0.9),"Acoustic Emission [dB]":(75,95),"Current Draw [A]":(9,16)},
    "Assembly Robot":             {"Air temperature [K]":(294,304),"Process temperature [K]":(302,314),"Rotational speed [rpm]":(300,800),"Torque [Nm]":(10,30),"Tool wear [min]":(0,60),"Vibration Sensor [g]":(0.1,0.3),"Acoustic Emission [dB]":(50,68),"Current Draw [A]":(4,8)},
    "Other":                      {"Air temperature [K]":(295,310),"Process temperature [K]":(305,320),"Rotational speed [rpm]":(1000,2000),"Torque [Nm]":(30,70),"Tool wear [min]":(0,150),"Vibration Sensor [g]":(0.2,0.8),"Acoustic Emission [dB]":(60,85),"Current Draw [A]":(8,15)},
}

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def generate_otp(): return ''.join(random.choices(string.digits, k=6))

def generate_machine_id(state, district, conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM machines WHERE state=? AND district=?", (state, district))
    fac_count = c.fetchone()[0] + 1
    return f"{state[:2].upper()}-{district[:3].upper()}-FAC{str(fac_count).zfill(3)}-MCH001"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables(conn):
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, username TEXT UNIQUE, password_hash TEXT,
        role TEXT, state TEXT, district TEXT,
        factory_name TEXT, machine_type TEXT, email TEXT,
        email_verified INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS machines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        machine_id TEXT UNIQUE, user_id INTEGER,
        machine_type TEXT, installation_date TEXT,
        last_service TEXT, next_service_due TEXT,
        state TEXT, district TEXT, factory_name TEXT,
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        machine_id TEXT, priority TEXT, rul REAL,
        failure_mode TEXT, action TEXT,
        acknowledged INTEGER DEFAULT 0,
        escalated INTEGER DEFAULT 0,
        sent_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS otp_store (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT, otp TEXT,
        expires_at TEXT,
        used INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    print("✅ Tables created!")

def seed_demo_data(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] > 0:
        print("Already seeded.")
        return
    now = datetime.now()
    c.execute("INSERT INTO users (name,username,password_hash,role,email,email_verified) VALUES (?,?,?,?,?,?)",
              ("Super Admin","superadmin",hash_password("super123"),"superadmin","admin@sentineliq.com",1))
    c.execute("INSERT INTO users (name,username,password_hash,role,state,email,email_verified) VALUES (?,?,?,?,?,?,?)",
              ("Amit Shah","mh_admin",hash_password("mhpass123"),"state_admin","Maharashtra","amit@sentineliq.com",1))
    c.execute("INSERT INTO users (name,username,password_hash,role,state,district,email,email_verified) VALUES (?,?,?,?,?,?,?,?)",
              ("Priya Desai","pune_admin",hash_password("punepass123"),"district_admin","Maharashtra","Pune","priya@sentineliq.com",1))
    demos = [
        ("Rajesh Kumar","factory1","fact1pass","Maharashtra","Pune","Pune Precision Parts","CNC Milling Machine","rajesh@factory.com",12,3),
        ("Suresh Patel","factory2","fact2pass","Gujarat","Surat","Surat Textile Machines","Industrial Lathe","suresh@factory.com",28,1),
        ("Vikram Sharma","factory3","fact3pass","Maharashtra","Nashik","Nashik Auto Components","Hydraulic Press","vikram@factory.com",45,-5),
        ("Anita Singh","factory4","fact4pass","Karnataka","Bengaluru Urban","Bengaluru Electronics","Assembly Robot","anita@factory.com",5,10),
    ]
    for name,uname,pwd,state,dist,factory,mtype,email,last_days,next_days in demos:
        c.execute("INSERT INTO users (name,username,password_hash,role,state,district,factory_name,machine_type,email,email_verified) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (name,uname,hash_password(pwd),"manager",state,dist,factory,mtype,email,1))
        uid = c.lastrowid
        mid = generate_machine_id(state, dist, conn)
        c.execute("INSERT INTO machines (machine_id,user_id,machine_type,installation_date,last_service,next_service_due,state,district,factory_name) VALUES (?,?,?,?,?,?,?,?,?)",
                  (mid,uid,mtype,(now-timedelta(days=365*5)).strftime("%Y-%m-%d"),
                   (now-timedelta(days=last_days)).strftime("%Y-%m-%d"),
                   (now+timedelta(days=next_days)).strftime("%Y-%m-%d"),
                   state,dist,factory))
    conn.commit()
    print("✅ Demo data seeded!")
    print("\n─────────────────────────────────────────────────")
    print(f"{'Role':<25} {'Username':<15} {'Password'}")
    print("─────────────────────────────────────────────────")
    print(f"{'Super Admin':<25} {'superadmin':<15} super123")
    print(f"{'State Admin (MH)':<25} {'mh_admin':<15} mhpass123")
    print(f"{'District Admin (Pune)':<25} {'pune_admin':<15} punepass123")
    print(f"{'Manager 1 (Pune)':<25} {'factory1':<15} fact1pass")
    print(f"{'Manager 2 (Surat)':<25} {'factory2':<15} fact2pass")
    print(f"{'Manager 3 (Nashik)':<25} {'factory3':<15} fact3pass")
    print(f"{'Manager 4 (Bengaluru)':<25} {'factory4':<15} fact4pass")
    print("─────────────────────────────────────────────────")

# ── HELPER FUNCTIONS ──
def verify_login(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, hash_password(password)))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_machines_for_user(user):
    conn = get_connection()
    c = conn.cursor()
    role = user["role"]
    if role == "superadmin":
        c.execute("SELECT * FROM machines ORDER BY state,district,factory_name")
    elif role == "state_admin":
        c.execute("SELECT * FROM machines WHERE state=? ORDER BY district,factory_name", (user["state"],))
    elif role == "district_admin":
        c.execute("SELECT * FROM machines WHERE state=? AND district=? ORDER BY factory_name", (user["state"],user["district"]))
    else:
        c.execute("SELECT * FROM machines WHERE user_id=?", (user["id"],))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_users_by_role(role, state=None, district=None):
    conn = get_connection()
    c = conn.cursor()
    if district:
        c.execute("SELECT * FROM users WHERE role=? AND state=? AND district=?", (role,state,district))
    elif state:
        c.execute("SELECT * FROM users WHERE role=? AND state=?", (role,state))
    else:
        c.execute("SELECT * FROM users WHERE role=?", (role,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def check_admin_exists(role, state=None, district=None):
    """
    Check if admin already exists for given state/district.
    Returns (exists: bool, message: str)
    """
    conn = get_connection()
    c = conn.cursor()
    if role == "state_admin" and state:
        c.execute("SELECT name FROM users WHERE role='state_admin' AND state=?", (state,))
        row = c.fetchone()
        conn.close()
        if row:
            return True, f"State Admin for {state} already exists ({row['name']}). Only one State Admin allowed per state."
    elif role == "district_admin" and state and district:
        c.execute("SELECT name FROM users WHERE role='district_admin' AND state=? AND district=?", (state,district))
        row = c.fetchone()
        conn.close()
        if row:
            return True, f"District Admin for {district}, {state} already exists ({row['name']}). Only one District Admin allowed per district."
    conn.close()
    return False, ""

def create_user(name, username, password, role, state=None, district=None,
                factory_name=None, machine_type=None, email=None, email_verified=1):
    conn = get_connection()
    c = conn.cursor()

    # check username unique
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    if c.fetchone():
        conn.close()
        return None, "Username already exists. Please choose a different username."

    # check one admin per state
    if role == "state_admin" and state:
        c.execute("SELECT name FROM users WHERE role='state_admin' AND state=?", (state,))
        row = c.fetchone()
        if row:
            conn.close()
            return None, f"❌ State Admin for {state} already exists ({row['name']}). Only one State Admin is allowed per state."

    # check one admin per district
    if role == "district_admin" and state and district:
        c.execute("SELECT name FROM users WHERE role='district_admin' AND state=? AND district=?", (state,district))
        row = c.fetchone()
        if row:
            conn.close()
            return None, f"❌ District Admin for {district}, {state} already exists ({row['name']}). Only one District Admin is allowed per district."

    # create user
    c.execute("""INSERT INTO users (name,username,password_hash,role,state,district,
                 factory_name,machine_type,email,email_verified)
                 VALUES (?,?,?,?,?,?,?,?,?,?)""",
              (name,username,hash_password(password),role,state,district,
               factory_name,machine_type,email,email_verified))
    user_id = c.lastrowid
    machine_id = None

    # create machine for manager
    if role == "manager" and state and district:
        machine_id = generate_machine_id(state, district, conn)
        now = datetime.now()
        c.execute("""INSERT INTO machines (machine_id,user_id,machine_type,installation_date,
                     last_service,next_service_due,state,district,factory_name)
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (machine_id,user_id,machine_type or "Other",
                   now.strftime("%Y-%m-%d"),now.strftime("%Y-%m-%d"),
                   (now+timedelta(days=90)).strftime("%Y-%m-%d"),
                   state,district,factory_name))
    conn.commit()
    conn.close()
    return machine_id or "Created", "Success"

def get_manager_email_for_machine(machine_id):
    """Get the registered email of manager who owns this machine."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT u.email, u.name FROM machines m
                 JOIN users u ON m.user_id = u.id
                 WHERE m.machine_id=?""", (machine_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_higher_authority_email(machine_id):
    """Get district admin or state admin email for escalation."""
    conn = get_connection()
    c = conn.cursor()
    # get machine state/district
    c.execute("SELECT state, district FROM machines WHERE machine_id=?", (machine_id,))
    m = c.fetchone()
    if not m:
        conn.close()
        return None
    # try district admin first
    c.execute("SELECT email,name FROM users WHERE role='district_admin' AND state=? AND district=?",
              (m["state"], m["district"]))
    row = c.fetchone()
    if not row:
        # try state admin
        c.execute("SELECT email,name FROM users WHERE role='state_admin' AND state=?", (m["state"],))
        row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def save_otp(email, otp):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM otp_store WHERE email=?", (email,))
    expires = (datetime.now() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO otp_store (email,otp,expires_at) VALUES (?,?,?)", (email,otp,expires))
    conn.commit()
    conn.close()

def verify_otp(email, otp):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM otp_store WHERE email=? AND otp=? AND used=0", (email,otp))
    row = c.fetchone()
    if not row:
        conn.close()
        return False, "Invalid OTP. Please check and try again."
    expires = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S")
    if datetime.now() > expires:
        conn.close()
        return False, "OTP expired. Please request a new one."
    c.execute("UPDATE otp_store SET used=1 WHERE email=? AND otp=?", (email,otp))
    conn.commit()
    conn.close()
    return True, "Success"

def get_machine_by_id(machine_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM machines WHERE machine_id=?", (machine_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_alerts_for_machine(machine_id, limit=20):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM alerts WHERE machine_id=? ORDER BY sent_at DESC LIMIT ?", (machine_id,limit))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def log_alert(machine_id, priority, rul, failure_mode, action):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO alerts (machine_id,priority,rul,failure_mode,action) VALUES (?,?,?,?,?)",
              (machine_id,priority,rul,failure_mode,action))
    conn.commit()
    conn.close()

def get_all_states(): return sorted(INDIA_DATA.keys())
def get_districts(state): return sorted(INDIA_DATA.get(state, []))
def get_machine_types(): return MACHINE_TYPES
def get_sensor_ranges(mtype): return SENSOR_RANGES.get(mtype, SENSOR_RANGES["Other"])

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        ans = input(f"⚠️  {DB_PATH} exists. Reset? (yes/no): ").strip().lower()
        if ans == "yes":
            os.remove(DB_PATH)
            print("Old database removed.")
        else:
            print("Keeping existing database.")
            exit()
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    seed_demo_data(conn)
    conn.close()
    print(f"\n✅ Database ready: {DB_PATH}")
