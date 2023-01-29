import email
import os
from click import password_option
from flask import Flask, session, render_template, request, redirect, url_for, flash
from flask_dropzone import Dropzone
import secrets
import pyrebase 


from wtforms import TextAreaField, SubmitField, SelectField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length

from werkzeug.utils import secure_filename





# OCR
import cv2
import pytesseract
from PIL import Image
import numpy as np

# pip install gTTS
from gtts import gTTS

from cv2 import triangulatePoints







app = Flask(__name__)


dir_path = os.path.dirname(os.path.realpath(__file__))
app.config.update(
    UPLOADED_PATH = os.path.join(dir_path, "static/uploaded_files/"),
    DROPZONE_ALLOWED_FILE_TYPE = "image",
    DROPZONE_MAX_FILE_SIZE = 3,
    DROPZONE_MAX_FILES =1,
    AUDIO_FILE_UPLOAD = os.path.join(dir_path, "static/audio_files/")


)

app.config['DROPZONE_REDIRECT_VIEW'] = 'decoded'

dropzone = Dropzone(app)

config = {
  'apiKey': "AIzaSyC_mPoW2BYUfWrJYuI3Vr-ngC6_xDd_iRc",
  'authDomain': "texttoaudio1-20b3a.firebaseapp.com",
  'databaseURL': "https://texttoaudio1-20b3a-default-rtdb.asia-southeast1.firebasedatabase.app",
  'projectId': "texttoaudio1-20b3a",
  'storageBucket': "texttoaudio1-20b3a.appspot.com",
  'messagingSenderId': "1004726950657",
  'appId': "1:1004726950657:web:2adc22c65f081947b95900",
  'measurementId': "G-SXMJ9CMV4E"
}



firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()






app.secret_key = 'agdhgahghad adhjjahdjadhj'



	


##API##
@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if (request.method == 'POST'):
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            user = auth.create_user_with_email_and_password(email, password)

            user_info = {
                'username': username,
                'email': email,
                'password': password
            }

            db.child('users').child(user['localId']).push(user_info)
            
            
            

            return render_template('login.html')
    return render_template('create_account.html')



@app.route('/')
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session['user'] = email   
            successful = 'Hi, {}' .format(session['user'])
            return render_template('index.html', smessage=successful)
        except:
            unsuccessful = 'Please check your credentials'
            return render_template('login.html', umessage=unsuccessful)
    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if (request.method == 'POST'):
            email = request.form['email']
            auth.send_password_reset_email(email)
            return render_template('login.html')
    return render_template('forgot_password.html')

@app.route('/index', methods=['GET', 'POST'])


@app.route('/book_info', methods=['GET','POST'] )
def book_info():
   if (request.method == 'POST'): 
        booktitle = request.form['booktitle']
        author = request.form['author']
        book_info = {
                'booktitle': booktitle,
                'author': author,
            }
        db.child('users').child(auth.current_user["localId"]).push(book_info)
        return render_template('upload.html')
    


@app.route("/upload", methods=["GET", "POST"])
def upload():
   

    if request.method == 'POST':
       

        # set a session value
        sentence = ""
        
         # get the list of files from web
        f = request.files.get('file')
        # something.jpg >> ["something , jpg"]
        
        filename, extension = f.filename.split(".")
        generated_filename = secrets.token_hex(20) + f".{extension}"
        #storage.child("users/email/example.jpg").put("example2.jpg",email['email'])
       
        file_location = os.path.join(app.config['UPLOADED_PATH'], generated_filename)
        

        f.save(file_location)

    

        #storage.child("users/email/example.jpg").put("example2.jpg",email['email'])
    
    
        storage.child('users').child(auth.current_user["localId"]).child('book').child('image').put(file_location)

        # print(file_location)

        # OCR here
        pytesseract.pytesseract.tesseract_cmd = "/app/.apt/usr/bin/tesseract"
        img = cv2.imread(file_location)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


        boxes = pytesseract.image_to_data(img)
        # print(boxes)
    
        for i, box in enumerate(boxes.splitlines()):
            if i == 0:
                continue

            box = box.split()
            # print(box)

            # only deal with boxes with word in it.
            if len(box) == 12:
                sentence += box[11] + " "
       
        print(sentence)
        session["sentence"] = sentence


        # delete file after you are done working with it
        os.remove(file_location)

        return redirect("/decoded/")

    else:
       return render_template("upload.html", title="Upload")

class QRCodeData(FlaskForm):
    data_field = TextAreaField('Converted Text:', 
                            validators=[DataRequired(), 
                            Length(min=1, max=100000000000)]
    )
    submit = SubmitField('Convert to Audio') 


@app.route("/decoded", methods=["GET", "POST"])
def decoded():
    
   
    sentence = session.get("sentence")
    

    
    # print(sentence)

    # print(lang)
    
    # print(lang, conf)
    

    form =QRCodeData() 

    if request.method == "POST":
        
        
        
        generated_audio_filename = secrets.token_hex(10) + ".mp4"
        text_data = form.data_field.data
        # print("Data here", translate_to)

  
        
        print(text_data)
       

        

        tts = gTTS(text_data)



        file_location = os.path.join(
                            app.config['AUDIO_FILE_UPLOAD'], 
                            generated_audio_filename
                        )

        # save file as audio
        tts.save(file_location)
        storage.child('users').child(auth.current_user["localId"]).child('book').child('audio').put(file_location)

        # return redirect("/audio_download/" + generated_audio_filename)

        form.data_field.data = text_data

        return render_template("decoded.html", 
                        title="Decoded", 
                        form=form, 
                        audio = True,
                        file = generated_audio_filename
                    )


    # form.data_field.data = sentence
    form.data_field.data = sentence

    # set the sentence back to defautl blank
    # sentence = ""
    session["sentence"] = ""

    return render_template("decoded.html", 
                            title="Decoded", 
                            form=form, 
                            audio = False
                        )


    


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.pop('user')
    return redirect('/login/')




if __name__ == '__main__':
    app.run(port=1111)

    