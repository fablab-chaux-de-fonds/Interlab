import re
import psycopg2
from dateutil import parser
from accounts.models import CustomUser as User, Profile, Subscription, SubscriptionCategory
from machines.models import Training, TrainingValidation
from django.contrib.auth.models import Group

# Fill with the expected list of super users emails
superuser_list = []

# Mapping between fabmanager trainings and interlab trainings
newTrainings = Training.objects.all()
trainings = dict({(e[0], newTrainings.get(title=e[1])) for e in {
    ('decoupeuse-laser', 'Découpeuse et graveuse laser'), 
    ('formation-cnc-mach3', 'CNC'), 
    ('formation-imprimante-3d', 'Imprimante 3D'), 
    ('formation-fao-vcarve', 'FAO VCarve'), 
    ('decoupeuse-vinyle', 'Découpeuse vinyle')
}})

# Mapping between fabmanager plans subscription and interlab substription
newCategories = SubscriptionCategory.objects.all()
categories = dict({(e[0], newCategories.get(title=e[1])) for e in {
    ('Demi-tarif', 'Demi-Tarif'), 
    # ('Pack institution'), 
    # ('Pack entreprise'), 
    # ('Pack multi-sites'), 
    ('Demi-tarif Etudiant', 'Demi-tarif étudiant·e')
}})

# Expect a superuser group in database (not the flag is_superuser)
superuser = Group.objects.get(name='superuser')

with psycopg2.connect("dbname=fabmanager host=db user=postgres password=postgres") as conn:
    with conn.cursor() as cur:
        cur.execute('''select profiles.first_name, 
profiles.last_name, 
profiles.phone, 
users.email, 
users.is_active, 
users.encrypted_password, 
users.created_at,
(select CASE WHEN 'admin' = ANY(ARRAY_AGG(roles.name)) THEN 1::boolean ELSE 0::boolean END from users_roles inner join roles on roles.id = users_roles.role_id where users_roles.user_id = users.id group by users_roles.user_id) as is_admin,
(select json_build_object('title', base_name, 'start', subscriptions.updated_at, 'end', expired_at)
from subscriptions 
 join plans on plans.id = subscriptions.plan_id
 where subscriptions.user_id = users.id 
    and subscriptions.expired_at > (now() at time zone 'utc')
	and plans.disabled is null) as subscription,
(select json_agg(trainings.slug) from user_trainings
 join trainings on trainings.id = user_trainings.training_id
 where user_id = users.id) as trainings
from users 
inner join profiles on users.id = profiles.user_id;''')
        oldUser = cur.fetchone()
        while oldUser:
            newUser = User.objects.filter(email=oldUser[3]).first()
            try:
                if None == newUser:
                    try:
                        newUsername = re.sub('[^a-z]+', '', oldUser[0].lower())[0]+re.sub('[^a-z]+', '', oldUser[1].lower())
                    except:
                        newUsername = re.sub('@.+', '', oldUser[3]) # Special case for non-ascii usernames
                    newUserCount = User.objects.filter(username=newUsername).count()
                    while User.objects.filter(username=newUsername+str(newUserCount)).count() > 0:
                        newUserCount += 1
                    if newUserCount > 0:
                        newUsername += str(newUserCount)
                    newUser = User.objects.create_user(newUsername, oldUser[3], None)
                newUser.password = 'bcrypt${}'.format(oldUser[5])
                newUser.first_name = oldUser[0]
                newUser.last_name = oldUser[1]
                newUser.is_staff = oldUser[7]
                newUser.date_joined = oldUser[6]
                if newUser.email in superuser_list:
                    newUser.is_superuser = True
                else:
                    newUser.is_superuser = False
                newUser.save()
                newProfile = Profile.objects.filter(user=newUser).first()
                if newProfile == None:
                    newProfile = Profile.objects.create(user=newUser, subscription=None)
                newProfile.save()
                if oldUser[8] != None:
                    newSubscriptionCategory = categories[oldUser[8]['title']]
                    newSubscription = Subscription.objects.create(profile=newProfile, start=parser.parse(oldUser[8]['start']),end=parser.parse(oldUser[8]['end']),subscription_category=newSubscriptionCategory,access_number=newSubscriptionCategory.default_access_number)
                    newSubscription.save()
                if newUser.is_staff:
                    superuser.user_set.add(newUser)
                if oldUser[9] != None:
                    TrainingValidation.objects.filter(profile=newProfile).delete()
                    for slug in oldUser[9]:
                        TrainingValidation.objects.create(profile=newProfile,training=trainings[slug]).save()
                print('{} {}'.format(newUser.username, newUser.email))
            except:
                print('ERROR: {}'.format(oldUser))
                raise
            oldUser = cur.fetchone()
        superuser.save()

