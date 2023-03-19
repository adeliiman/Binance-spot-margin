import json, threading, time
from flask import Flask, request, render_template
from forms import UserSettingForm
from models import UserSetting, Position
from main import  handle_webhook


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Binance.db'
app.config['SECRET_KEY'] = 'abc8123def%&*SHA16x16'

from extensions import db
db.init_app(app)


@app.route('/', methods=['POST', 'GET'])
def index():
	form = UserSettingForm(request.form)

	user = db.session.execute(db.select(UserSetting).order_by(UserSetting.id.desc())).scalar()
	if request.method == "POST":
		data = request.form.to_dict()
		#print(data)

		risk = data['risk']
		spot = data['spot']
		
		if not user:
			setting = UserSetting()
			setting.risk = risk
			setting.spot = spot
			db.session.add(setting)
			db.session.commit()
		else:
			if risk: user.risk = risk
			if spot: user.spot = spot
			db.session.commit()

	user = db.session.execute(db.select(UserSetting).order_by(UserSetting.id.desc())).scalar()
	orders = db.session.execute(db.select(Position).limit(10).order_by(Position.id.desc())).scalars()
	return render_template("index.html", form=form, orders=orders, user=user)
	

@app.route("/webhook", methods=['POST'])
def webhook():
	
	webhook_passphrase = "SHA16x16@gmail.com"
	data = json.loads(request.data)
	
	if 'passphrase' not in data.keys():
		return {
		"success": False,
		"message": "no passphrase entered"
		}

	if data['passphrase'] != webhook_passphrase:
		return {
		"success": False,
		"message": "invalid passphrase"
		}

	orders = handle_webhook(data)
	return "200"

with app.app_context():
	db.create_all()


def web():
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)
	#from waitress import serve
	#serve(app, host="0.0.0.0", port=5000)


if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=5000)

"""
if __name__ == '__main__':
	threading.Thread(target=web, daemon=True).start()
	#threading.Thread(target=handle_socket, args=(), daemon=True).start()

	while True:
		time.sleep(1) 

"""
