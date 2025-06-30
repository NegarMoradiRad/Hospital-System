from flask import Flask,url_for,render_template,request,redirect
from pymongo import MongoClient
import re

client=MongoClient("mongodb://localhost:27017/")
db=client["hospitals_resumes"]
collection1=db['hospitals_selected']
collection2=db["resumes"]
collection3=db["hospitals"]
collection4=db["userip"]

app=Flask(__name__)

upload_folder = "static/uplouds" 
app.config["UPLOAD_FOLDER"] = upload_folder

hospitals_name=[]
hospitals_name_slug=[]
query_params=[]

def is_safe_image(filename):
   allowed=["png","jpg"]
   if filename.split(".")[-1] not in allowed:
      return True
   
def is_safe_file(filename):
   allowed=["pdf"]
   if filename.split(".")[-1] not in allowed:
      return True

@app.route("/")
def homepage():
    document=collection3.find({}, {"_id": 0, "نام بیمارستان": 1})
    hospitals=[]
    for hospital in document:
       hospitals.append(hospital["نام بیمارستان"])

    return render_template("index.html",hospitals=hospitals)

@app.route("/select", methods=["POST"])
def select():
    global hospitals_name
    global hospitals_name_slug
    global query_params
    hospitals_name = request.form.getlist("HospitalsName")     
    hospitals_name_slug=[name.replace(' ', '-') for name in hospitals_name]
    query_params = "&".join([f"name={name}" for name in hospitals_name_slug])
    document1 = {
        "hospitals_name": hospitals_name,
        'sluge_name':hospitals_name_slug
    }

    collection1.insert_one(document1)
    error=[]
    if not hospitals_name:
       error.append("لطفا بیمارستان مورد نظر برای ارسال رزومه را انتخاب کنید")
    if error:
       return render_template("index.html", error=error)
    tag=1
    for i in collection4.find({}, {"_id": 0, "ip": 1}):
       if request.remote_addr in collection4.find({}, {"_id": 0, "ip": 1}):
        tag=1
    if tag != 1:
       return redirect('/registerpage')
    else:
      return redirect('/loginpage')
    #return redirect(f"/form?{query_params}")

@app.route("/AddHospital")
def AddHospital():
   return redirect("/Addform")

@app.route("/Addform", methods=["GET","POST"])
def addform():
  if request.method == "GET":
    return render_template ('addform.html')
  
  name=request.form.get('name','').strip()
  address=request.form.get('address','').strip()
  id=request.form.get('id','').strip()

  validinput=re.compile(r'^[\w\u0600-\u06FF\s]{2,50}$')
  errors=[]
  if not name or not address or not id:
      errors.append("پر کردن تمامی فیلدها الزامی است")
  if  not validinput.match(name):
      errors.append("نام بیمارستان نامعتبر است")
      
  if address and not validinput.match(address):
      errors.append("خطا:کاراکتر های غیرمجاز در فیلد آدرس")

  if errors:
    return render_template("addform.html",errors=errors)

  document3={
      "نام بیمارستان":name,
      "شناسه ثبت":id,
      "آدرس بیمارستان":address
   }
  collection3.insert_one(document3)
  return render_template("addform.html",send=True)



@app.route("/form", methods=["GET","POST"])
def form():
    if request.method == "GET":
     parameters = request.args.getlist("name")
     return render_template("form.html", par=parameters)


    image=request.files.get("image")
    resume=request.files.get("file")
    image_name=image.filename
    resume_name=resume.filename
    
    fname=request.form.get("fname","").strip()
    lname=request.form.get("lname","").strip()
    gender=request.form.get("gender","").strip()
    position=request.form.get("position","").strip()
    
    validFname=re.compile(r'^[\w\u0600-\u06FF\s]{2,50}$')
    validLname=re.compile(r'^[\w\u0600-\u06FF\s]{2,50}$')
    errors=[]
    if not gender:
       errors.append("لطفا جنسیت را وارد کنید")
    if not position:
       errors.append("لطفا پوزیشن کاری خود را انتخاب کنید")
    if not fname or not lname or not image_name or not resume_name:
       errors.append("پر کردن تمام فیلدها الزامیست")
    if fname and not validFname.match(fname):
       errors.append("فرمت نام وارد شده نامعتبر است")
    if  lname and not validLname.match(lname):
        errors.append("فرمت نام خانوادگی وارد شده نامعتبر است")
    if resume_name and is_safe_file(resume_name):
       errors.append("فرمت فایل وارد شده اشتباه است")
    if image_name and is_safe_image(image_name):
       errors.append("فرمت تصویر وارد شده نادرست است")
       

    if errors:
        # اگر اروری وجود داشت، دوباره فرم را با نمایش ارورها رندر کن
        parameters = request.form.getlist("hospitals_name")
        return render_template("form.html", par=parameters, errors=errors)
    
    image.save(f'{upload_folder}/{image_name}')
    resume.save(f'{upload_folder}/{resume_name}')

    document2={
        "نام":fname,
        "نام خانوادگی":lname,
        "عکس پرسنلی":image.filename,
        'پوزیشن انتخابی':position,
        "جنسیت":gender,
        "فایل رزومه":resume.filename,
        "بیمارستانهای انتخابی":request.form.getlist("hospitals_name")
    }
    collection2.insert_one(document2)
    return render_template('form.html', send=True)

@app.route("/login")
def login():
   pass

@app.route("/loginpage")
def loginpage():
   return render_template("login.html")

@app.route("/register")
def register():
   user_ip=request.remote_addr
   document4={
      'ip':user_ip
   }
   collection4.insert_one(document4)
   return redirect("/registerpage")
@app.route("/registerpage")
def registerpage():
   return render_template("/register.html")
if __name__=="__main__":
    app.run(debug=True)