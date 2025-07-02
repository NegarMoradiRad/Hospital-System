from flask import Flask,url_for,render_template,request,redirect
from pymongo import MongoClient
import re

client=MongoClient("mongodb://localhost:27017/")
db=client["hospitals_resumes"]
collection1=db['hospitals_selected']
collection2=db["resumes"]
collection3=db["hospitals"]
collection4=db["users"]

app=Flask(__name__)

upload_folder = "static/uplouds" 
app.config["UPLOAD_FOLDER"] = upload_folder


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
    hospitals_name = request.form.getlist("HospitalsName")     
    error=[]

    if not hospitals_name:
       error.append("لطفا بیمارستان مورد نظر برای ارسال رزومه را انتخاب کنید")
    if error:
       return render_template("index.html", error=error)
    
    return redirect('/registerpage')
    

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
     email=request.args.get("email")
     return render_template("form.html", par=parameters,email=email)


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
        return render_template("form.html", par=parameters, errors=errors,email=email)
    
    image.save(f'{upload_folder}/{image_name}')
    resume.save(f'{upload_folder}/{resume_name}')

    document2={
        "نام":fname,
        "نام خانوادگی":lname,
        "عکس پرسنلی":image.filename,
        'پوزیشن انتخابی':position,
        "جنسیت":gender,
        "فایل رزومه":resume.filename,
        "بیمارستانهای انتخابی":request.form.getlist("hospitals_name"),
        "ایمیل":request.form.get("email")
    }
    collection2.insert_one(document2)

    return render_template('form.html', send=True)

@app.route("/login", methods=['POST'])
def login():
   email=request.form.get('email','').strip()
   password=request.form.get('password','').strip()
   user=collection4.find_one({"ایمیل":email})
  
   resumes=[]
   for resume in collection2.find({"ایمیل":email}):
      resumes.append(resume)

   errors=[]
   document=collection3.find({}, {"_id": 0, "نام بیمارستان": 1})
   hospitals=[]
   for hospital in document:
       hospitals.append(hospital["نام بیمارستان"])

   if user:
      if password == user.get("رمز عبور"):
            return render_template("user.html", information=user ,hospitals=hospitals ,email=email ,resumes=resumes)
      else:
            errors.append("رمز عبور نادرست است")
   else:
        errors.append("حساب کاربری با این ایمیل یافت نشد")

   if errors:
      return render_template("login.html",errors=errors)
   
@app.route("/loginpage")
def loginpage():
   return render_template("login.html")

@app.route("/register",  methods=["POST"])
def register():
   user_ip=request.remote_addr
   email=request.form.get('email','').strip()
   fullname=request.form.get('fullname','').strip()
   password=request.form.get('password','').strip()

   validname=re.compile(r'^[\w\u0600-\u06FF\s]{2,50}$')
   validemail=re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
   validpassword=re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
   errors=[]
   if not email or not password or not fullname:
      errors.append("پر کردن تمام فیلدها الزامیست")

   if not validemail.match(email) and email:
      errors.append("ایمیل وارد شده نا معتبر است")
   
   if not validname.match(fullname) and fullname:
      errors.append("نام وارد شده نامعتبر است")

   if not validpassword.match(password) and password:
      errors.append("رمز عبور تنظیم شده نامعتبر است")

   if email in collection4.find({}, {"_id": 0, "ایمیل": 1}):
      errors.append("شما قبلا با این ایمیل ثبت نام کرده اید")

   if errors:
      return render_template("register.html",errors=errors)
   
   
   document4={
      'ip':user_ip,
       'نام و نام خانوادگی':fullname,
       'ایمیل':email,
       'رمز عبور':password
   }
   collection4.insert_one(document4)

   return render_template("register.html",send=True)

@app.route("/registerpage")
def registerpage():
   return render_template("/register.html")

@app.route('/userpage',methods=['POST'])
def userpage():
   email=request.form.get("email")
   hospitals_name = request.form.getlist("HospitalsName")     
   hospitals_name_slug=[name.replace(' ', '-') for name in hospitals_name]
   query_params = "&".join([f"name={name}" for name in hospitals_name_slug])
   query_params2=f"&email={email}"
   document1 = {
        "hospitals_name": hospitals_name,
        'sluge_name':hospitals_name_slug
    }

   collection1.insert_one(document1)

   user=collection4.find_one({"ایمیل":email})   

   error=[]
   if not hospitals_name:
       error.append("لطفا بیمارستان مورد نظر برای ارسال رزومه را انتخاب کنید")
   if error:
       return render_template("user.html", error=error , information=user)
   
   return redirect(f"/form?{query_params}{query_params2}")

if __name__=="__main__":
    app.run(debug=True)