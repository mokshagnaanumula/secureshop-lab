from flask import Flask, request, session, redirect, url_for, render_template, abort, g, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os, sqlite3
from pathlib import Path
from functools import wraps
app=Flask(__name__); app.secret_key=os.getenv('SECRET_KEY','lab-only-change-this-secret')
SECURE=os.getenv('SECURE_MODE','0')=='1'; DB=Path(__file__).with_name('secureshop.db')
PRODUCTS=[(1,'Laptop','Everyday work laptop',899),(2,'Headphones','Noise-reducing headphones',149),(3,'Keyboard','Compact mechanical keyboard',79)]
def db():
 if 'db' not in g: g.db=sqlite3.connect(DB); g.db.row_factory=sqlite3.Row
 return g.db
@app.teardown_appcontext
def close_db(e=None):
 c=g.pop('db',None)
 if c: c.close()
def init_db():
 c=sqlite3.connect(DB); c.executescript('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE,password TEXT,is_admin INTEGER DEFAULT 0); CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY,user_id INTEGER,item TEXT,total REAL);')
 if not c.execute('SELECT 1 FROM users LIMIT 1').fetchone():
  for u,p,a in [('alice','alice123',0),('bob','bob123',0),('admin','admin123',1)]: c.execute('INSERT INTO users(username,password,is_admin) VALUES(?,?,?)',(u,generate_password_hash(p) if SECURE else p,a))
  c.executemany('INSERT INTO orders(user_id,item,total) VALUES(?,?,?)',[(1,'Laptop',899),(2,'Headphones',149)]); c.commit()
 c.close()
def user():
 i=session.get('uid'); return db().execute('SELECT id,username,is_admin FROM users WHERE id=?',(i,)).fetchone() if i else None
def login_required(f):
 @wraps(f)
 def w(*a,**k):
  if not user(): return redirect(url_for('login'))
  return f(*a,**k)
 return w
def admin_required(f):
 @wraps(f)
 def w(*a,**k):
  u=user()
  if not u or not u['is_admin']: abort(403)
  return f(*a,**k)
 return w
@app.after_request
def headers(r):
 if SECURE:
  r.headers['Content-Security-Policy']="default-src 'self'; style-src 'self'; frame-ancestors 'none'"; r.headers['X-Content-Type-Options']='nosniff'; r.headers['X-Frame-Options']='DENY'; r.headers['Referrer-Policy']='strict-origin-when-cross-origin'
 return r
@app.route('/')
def home(): return render_template('home.html',products=PRODUCTS,user=user(),secure=SECURE)
@app.route('/products')
def products():
 q=request.args.get('q',''); source="(SELECT 1 id,'Laptop' name,'Everyday work laptop' description,899 price UNION ALL SELECT 2,'Headphones','Noise-reducing headphones',149 UNION ALL SELECT 3,'Keyboard','Compact mechanical keyboard',79)"
 try:
  rows=db().execute(f'SELECT * FROM {source} WHERE name LIKE ?',('%'+q+'%',)).fetchall() if SECURE else db().execute(f"SELECT * FROM {source} WHERE name LIKE '%{q}%' ").fetchall()
 except sqlite3.Error: rows=[]
 return render_template('products.html',products=rows,q=q,user=user())
@app.route('/register',methods=['GET','POST'])
def register():
 if request.method=='POST':
  u=request.form.get('username','').strip(); p=request.form.get('password','')
  try:
   db().execute('INSERT INTO users(username,password) VALUES(?,?)',(u,generate_password_hash(p) if SECURE else p)); db().commit(); flash('Account created. Log in now.'); return redirect(url_for('login'))
  except sqlite3.IntegrityError: flash('Username already registered.')
 return render_template('form.html',title='Register',user=user())
@app.route('/login',methods=['GET','POST'])
def login():
 if request.method=='POST':
  u=db().execute('SELECT * FROM users WHERE username=?',(request.form.get('username',''),)).fetchone(); p=request.form.get('password','')
  if u and (check_password_hash(u['password'],p) if SECURE else u['password']==p): session.clear(); session['uid']=u['id']; return redirect(url_for('home'))
  flash('Login failed.')
 return render_template('form.html',title='Login',user=user())
@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('home'))
@app.route('/profile')
@login_required
def profile(): return render_template('profile.html',user=user())
@app.route('/orders')
@login_required
def orders():
 u=user(); target=u['id'] if SECURE else request.args.get('user_id',str(u['id']))
 rows=db().execute('SELECT * FROM orders WHERE user_id=?',(target,)).fetchall() # IDOR on purpose in lab mode
 return render_template('orders.html',orders=rows,user=u)
@app.route('/cart',methods=['GET','POST'])
@login_required
def cart():
 if request.method=='POST' and request.form.get('item') in [p[1] for p in PRODUCTS]: session.setdefault('cart',[]).append(request.form['item'])
 return render_template('cart.html',cart=session.get('cart',[]),user=user())
@app.route('/admin')
@admin_required
def admin(): return render_template('admin.html',users=db().execute('SELECT id,username,is_admin FROM users').fetchall(),products=PRODUCTS,user=user())
@app.errorhandler(403)
def forbidden(e): return render_template('message.html',title='Forbidden',message='Administrator access required.',user=user()),403
if __name__=='__main__':
 init_db(); app.run(host='127.0.0.1',port=8080,debug=False)


