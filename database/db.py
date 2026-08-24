import os
import mysql.connector as mc
from dotenv import load_dotenv

load_dotenv()  # reads .env in your project root


class ChatBotDatabase:
    def __init__(self):
        self.conn = None
        self.cur = None
        try:
            connect_kwargs = dict(
                host=os.getenv("MYSQL_HOST"),
                port=int(os.getenv("MYSQL_PORT", "4000")),
                user=os.getenv("MYSQL_USER"),
                password=os.getenv("MYSQL_PASSWORD"),
                database=os.getenv("MYSQL_DATABASE"),
                autocommit=True,  # so every connection sees the latest
                                  # committed data immediately, instead of
                                  # reading a stale snapshot until this
                                  # connection's own next commit
            )

            # TiDB Cloud requires TLS. If you downloaded a CA cert (TiDB
            # Dedicated) put its path in MYSQL_CA_PATH; TiDB Serverless
            # usually works without one (just needs SSL enabled).
            ca_path = os.getenv("MYSQL_CA_PATH")
            if ca_path:
                connect_kwargs["ssl_ca"] = ca_path
                connect_kwargs["ssl_verify_cert"] = True
            else:
                connect_kwargs["ssl_disabled"] = False

            self.conn = mc.connect(**connect_kwargs)
            self.cur = self.conn.cursor(dictionary=True)
        except mc.Error as e:
            print(f"Database Connection Error: {e}")
            # Re-raise instead of silently continuing — otherwise every
            # method below fails later with a confusing, unrelated-looking
            # "'ChatBotDatabase' object has no attribute 'cur'" instead of
            # the actual connection error above.
            raise

    # यूज़र रजिस्ट्रेशन
    def register_user(self, name, email, mobile, password):
        sql = """INSERT INTO users(name, email, mobile, password) VALUES (%s, %s, %s, %s)"""
        self.cur.execute(sql, (name, email, mobile, password))
        self.conn.commit()

    # यूज़र लॉगिन
    # NOTE: confirmed via `DESCRIBE users;` that the live table only has
    # user_id, name, email, mobile, password — no `username`, no
    # `created_at`. Don't select columns that don't exist.
    def login_user(self, email, password):
        sql = """SELECT user_id, name, email, mobile, password
                  FROM users WHERE email=%s AND password=%s"""
        self.cur.execute(sql, (email, password))
        return self.cur.fetchone()

    # 🌟 किसी एक यूज़र की पूरी प्रोफ़ाइल user_id से निकालना (ProfileScreen के लिए)
    def get_users_by_id(self, user_id):
        sql = """SELECT user_id, name, email, mobile, password
                  FROM users WHERE user_id=%s"""
        self.cur.execute(sql, (user_id,))
        return self.cur.fetchone()

    # प्रोफ़ाइल अपडेट करने की सही और सुरक्षित लॉजिक
    def update_profile(self, user_id, name, email, mobile, password):
        sql = """
            UPDATE users 
            SET name=%s, email=%s, mobile=%s, password=%s 
            WHERE user_id=%s
        """
        self.cur.execute(sql, (name, email, mobile, password, user_id))
        self.conn.commit()

    # AI चैट को सेव करने का सही फ़ंक्शन (एरर फिक्स्ड)
    def save_ai_chat(self, user_id, user_massage, ai_response):
        sql = """
            INSERT INTO ai_chat_logs(user_id, user_massage, ai_response) 
            VALUES (%s, %s, %s)
        """
        self.cur.execute(sql, (user_id, user_massage, ai_response))
        self.conn.commit()

    # (बोनस) चैट हिस्ट्री को स्क्रीन पर दिखाने के लिए फ़ंक्शन
    def get_chat_history(self, user_id):
        sql = """SELECT * FROM ai_chat_logs WHERE user_id=%s ORDER BY created_at DESC"""
        self.cur.execute(sql, (user_id,))
        return self.cur.fetchall()

    # 🌟 किसी एक चैट को आईडी के ज़रिए डेटाबेस से डिलीट करना
    # user_id भी चेक करता है ताकि कोई और यूज़र किसी और का chat_id गेस
    # करके उसकी चैट डिलीट न कर सके
    def delete_chat(self, chat_id, user_id):
        sql = "DELETE FROM ai_chat_logs WHERE id = %s AND user_id = %s"
        self.cur.execute(sql, (chat_id, user_id))
        self.conn.commit()

    # 🌟 किसी एक पुरानी चैट पर क्लिक करने पर उसका पूरा डेटा निकालना
    # user_id भी चेक करता है, वही ownership वाली सुरक्षा यहाँ भी
    def get_single_chat(self, chat_id, user_id):
        sql = "SELECT * FROM ai_chat_logs WHERE id = %s AND user_id = %s"
        self.cur.execute(sql, (chat_id, user_id))
        return self.cur.fetchone()