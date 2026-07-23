import os
from flask import Flask, request, render_template, jsonify, session, redirect, url_for
import pymysql

# 현재 파일(app.py)이 위치한 절대 경로 계산
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 경로를 명시적으로 지정하여 TemplateNotFound 및 정적 파일 인식 오류 방지
app = Flask(
    __name__, 
    static_folder=os.path.join(BASE_DIR, 'images'), 
    static_url_path='/images',
    template_folder=os.path.join(BASE_DIR, 'templates')
)

app.secret_key = 'your_secret_key_here' 

# MariaDB 연결 설정
db_config = {
    'host': 'localhost',
    'user': 'kosmo_user',
    'password': '1234',
    'db': 'kosmo_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# ==========================================
# 1. 메인 및 세션 제어 라우트
# ==========================================
@app.route('/')
def home():
    if 'userid' in session:
        return f"""
            <div style="font-family: 'Malgun Gothic', sans-serif; text-align: center; margin-top: 50px;">
                <h3>{session['username']}님 환영합니다. ({session['userid']})</h3>
                <a href="/logout"><button style="padding: 5px 15px; cursor: pointer;">로그아웃</button></a>
            </div>
        """
    return redirect(url_for('login_page'))


# ==========================================
# 2. 로그인 / 로그아웃 라우트
# ==========================================
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('MemberLogin.html')

@app.route('/login_process', methods=['POST'])
def login_process():
    userid = request.form.get('userid')
    userpwd = request.form.get('userpwd')
    
    conn = None
    try:
        conn = pymysql.connect(**db_config)
        with conn.cursor() as cursor:
            sql = "SELECT userid, username FROM member WHERE userid = %s AND userpwd = %s"
            cursor.execute(sql, (userid, userpwd))
            user = cursor.fetchone()
            
            if user:
                session['userid'] = user['userid']
                session['username'] = user['username']
                return """
                    <script>
                        alert('로그인에 성공했습니다!');
                        location.href = '/';
                    </script>
                """
            else:
                return """
                    <script>
                        alert('아이디 또는 비밀번호가 일치하지 않습니다.');
                        history.back();
                    </script>
                """
    except Exception as e:
        print(f"Login Error: {e}")
        return """
            <script>
                alert('로그인 처리 중 서버 오류가 발생했습니다.');
                history.back();
            </script>
        """
    finally:
        if conn: conn.close()

@app.route('/logout')
def logout():
    session.clear() 
    return """
        <script>
            alert('로그아웃 되었습니다.');
            location.href = '/login';
        </script>
    """


# ==========================================
# 3. 회원가입 및 중복확인 라우트
# ==========================================
@app.route('/register', methods=['GET'])
def register_page():
    return render_template('MemberRegist.html')

@app.route('/check_id', methods=['POST'])
def check_id():
    userid = request.json.get('userid')
    if not userid:
        return jsonify({'result': 'fail', 'message': '아이디를 입력해주세요.'})
    conn = None
    try:
        conn = pymysql.connect(**db_config)
        with conn.cursor() as cursor:
            sql = "SELECT COUNT(*) as count FROM member WHERE userid = %s"
            cursor.execute(sql, (userid,))
            row = cursor.fetchone()
            if row['count'] > 0:
                return jsonify({'result': 'duplicate', 'message': '이미 사용 중인 아이디입니다.'})
            else:
                return jsonify({'result': 'success', 'message': '사용 가능한 아이디입니다.'})
    except Exception as e:
        return jsonify({'result': 'error', 'message': '서버 오류가 발생했습니다.'})
    finally:
        if conn: conn.close()

@app.route('/register', methods=['POST'])
def register():
    userid = request.form.get('userid')
    userpwd = request.form.get('userpwd')
    username = request.form.get('username')
    gender = request.form.get('gender')
    
    birth_year = request.form.get('birth_year')
    birth_month = request.form.get('birth_month')
    birth_day = request.form.get('birth_day')
    birth = f"{birth_year}-{birth_month}-{birth_day}" if birth_year and birth_month and birth_day else None
    
    email1 = request.form.get('email1')
    email2 = request.form.get('email2')
    email = f"{email1}@{email2}" if email1 and email2 else None
    email_agree = request.form.get('email_agree')
    
    zipcode = request.form.get('zipcode')
    addr1 = request.form.get('addr1')
    addr2 = request.form.get('addr2')
    
    tel1 = request.form.get('tel1')
    tel2 = request.form.get('tel2')
    tel3 = request.form.get('tel3')
    tel = f"{tel1}-{tel2}-{tel3}" if tel1 else None
    
    mobile = f"{request.form.get('mobile1')}-{request.form.get('mobile2')}-{request.form.get('mobile3')}"
    sms_agree = request.form.get('sms_agree')
    
    interest = request.form.get('interest')
    join_path = request.form.get('join_path')

    conn = None
    try:
        conn = pymysql.connect(**db_config)
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO member (
                    userid, userpwd, username, gender, birth, email, email_agree, 
                    zipcode, addr1, addr2, tel, mobile, sms_agree, interest, join_path
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (userid, userpwd, username, gender, birth, email, email_agree,
                      zipcode, addr1, addr2, tel, mobile, sms_agree, interest, join_path)
            cursor.execute(sql, values)
        conn.commit()
        return "<script>alert('회원가입이 완료되었습니다!'); location.href='/login';</script>"
    except Exception as e:
        if conn: conn.rollback()
        print(f"Register Error: {e}")
        return "<script>alert('오류가 발생했습니다.'); history.back();</script>"
    finally:
        if conn: conn.close()


# ==========================================
# 4. 아이디 / 비밀번호 실제 DB 연동 찾기 라우트
# ==========================================
@app.route('/find_account', methods=['GET'])
def find_account_page():
    return render_template('MemberFind.html')

@app.route('/find_id', methods=['POST'])
def find_id():
    data = request.json
    username = data.get('username')
    contact_type = data.get('contact_type')  # 프론트에서 넘겨준 'mobile' 또는 'email'
    val = data.get('value')
    
    conn = None
    try:
        conn = pymysql.connect(**db_config)
        with conn.cursor() as cursor:
            # 선택 유형에 맞는 필드 매칭 동적 SQL
            if contact_type == 'mobile':
                sql = "SELECT userid FROM member WHERE username = %s AND mobile = %s"
            else:
                sql = "SELECT userid FROM member WHERE username = %s AND email = %s"
                
            cursor.execute(sql, (username, val))
            user = cursor.fetchone()
            
            if user:
                return jsonify({'result': 'success', 'userid': user['userid']})
            else:
                return jsonify({'result': 'fail', 'message': '입력하신 정보와 일치하는 아이디를 찾을 수 없습니다.'})
    except Exception as e:
        print(f"Find ID DB Error: {e}")
        return jsonify({'result': 'error', 'message': '서버 처리 중 데이터베이스 오류가 발생했습니다.'})
    finally:
        if conn: conn.close()

@app.route('/find_pw', methods=['POST'])
def find_pw():
    data = request.json
    userid = data.get('userid')
    username = data.get('username')
    contact_type = data.get('contact_type')  # 프론트에서 넘겨준 'mobile' 또는 'email'
    val = data.get('value')
    
    conn = None
    try:
        conn = pymysql.connect(**db_config)
        with conn.cursor() as cursor:
            # 선택 유형에 맞는 필드 매칭 동적 SQL
            if contact_type == 'mobile':
                sql = "SELECT userpwd FROM member WHERE userid = %s AND username = %s AND mobile = %s"
            else:
                sql = "SELECT userpwd FROM member WHERE userid = %s AND username = %s AND email = %s"
                
            cursor.execute(sql, (userid, username, val))
            user = cursor.fetchone()
            
            if user:
                return jsonify({'result': 'success', 'userpwd': user['userpwd']})
            else:
                return jsonify({'result': 'fail', 'message': '입력하신 회원 정보와 일치하는 비밀번호를 찾을 수 없습니다.'})
    except Exception as e:
        print(f"Find PW DB Error: {e}")
        return jsonify({'result': 'error', 'message': '서버 처리 중 데이터베이스 오류가 발생했습니다.'})
    finally:
        if conn: conn.close()


if __name__ == '__main__':
    app.run(debug=True, port=5000)