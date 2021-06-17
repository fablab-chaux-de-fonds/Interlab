import re
import psycopg2
from django.contrib.auth.models import User

with psycopg2.connect("dbname=fablab_development host=db user=postgres password=postgres") as conn:
    with conn.cursor() as cur:
        cur.execute('''select profiles.first_name, 
        profiles.last_name, 
        profiles.phone, 
        users.email, 
        users.is_active, 
        users.encrypted_password, 
        users.created_at,
        (select CASE WHEN 'admin' = ANY(ARRAY_AGG(roles.name)) THEN 1::boolean ELSE 0::boolean END from users_roles inner join roles on roles.id = users_roles.role_id where users_roles.user_id = users.id group by users_roles.user_id) as is_admin
        from users 
        inner join profiles on users.id = profiles.user_id;
        ''')
        oldUser = cur.fetchone()
        while oldUser:
            newUsername = re.sub('[^a-z]+', '', oldUser[0].lower())[0]+re.sub('[^a-z]+', '', oldUser[1].lower())
            newUserCount = User.objects.filter(username=newUsername).count()
            while User.objects.filter(username=newUsername+str(newUserCount)).count() > 0:
                newUserCount += 1
            if newUserCount > 0:
                newUsername += str(newUserCount)
            newUser = User.objects.create_user(newUsername, oldUser[3], None)
            newUser.password = 'bcrypt$' + oldUser[5]
            newUser.first_name = oldUser[0]
            newUser.last_name = oldUser[1]
            newUser.is_staff = oldUser[7]
            newUser.date_joined = oldUser[6]
            newUser.save()
            print(newUsername)
            oldUser = cur.fetchone()

