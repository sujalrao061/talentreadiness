from datetime import date
from .models import *
from .auth import hash_password

SKILLS=["Python","SQL","Pandas","NumPy","Scikit-learn","TensorFlow","PyTorch","Machine Learning","Deep Learning","NLP","Computer Vision","Transformers","Hugging Face","RAG","FastAPI","Docker","Kubernetes","AWS","GCP","Azure","Spark","Kafka","Airflow","React","Node.js","PostgreSQL","MongoDB","Git","Linux","Data Modeling","LangChain","MLOps"]
NAMES=[("Sarah Wilson","ML Engineer","Machine Learning"),("David Chen","Data Scientist","Data Science"),("Priya Patel","AI Engineer","AI Engineering"),("Marcus Lee","Data Engineer","Data Engineering"),("Elena Rodriguez","Software Engineer","Software Engineering"),("Aisha Khan","ML Engineer","Machine Learning"),("Noah Williams","Data Scientist","Data Science"),("Maya Thompson","AI Engineer","AI Engineering"),("Liam Brown","Data Engineer","Data Engineering"),("Olivia Davis","Software Engineer","Software Engineering"),("Ethan Moore","ML Engineer","Machine Learning"),("Sofia Garcia","Data Scientist","Data Science"),("James Martin","AI Engineer","AI Engineering"),("Amelia Taylor","Data Engineer","Data Engineering"),("Benjamin Anderson","Software Engineer","Software Engineering"),("Chloe Thomas","ML Engineer","Machine Learning"),("Daniel Jackson","Data Scientist","Data Science"),("Grace White","AI Engineer","AI Engineering"),("Henry Harris","Data Engineer","Data Engineering"),("Isabella King","Software Engineer","Software Engineering")]
PROJECTS=[("Fraud Detection Platform","Real-time ML fraud detection for payments",[('Python',4,5,True),('PyTorch',4,5,True),('SQL',3,4,True),('AWS',3,3,False),('Machine Learning',4,5,True)]),("Recommendation Engine","Personalized commerce recommendations",[('Python',4,5,True),('Machine Learning',4,5,True),('Spark',3,3,False),('SQL',3,3,True)]),("Customer Churn Prediction","Retention-risk modeling",[('Python',4,5,True),('Scikit-learn',4,4,True),('SQL',4,4,True)]),("Real-Time Data Pipeline","Streaming ingestion platform",[('Python',3,3,False),('Kafka',4,5,True),('Spark',4,5,True),('Airflow',3,4,True)]),("LLM Knowledge Assistant","Internal knowledge search assistant",[('Python',4,5,True),('NLP',4,5,True),('RAG',4,5,True),('FastAPI',3,3,False)]),("Computer Vision Inspection","Quality inspection automation",[('Python',4,5,True),('Computer Vision',4,5,True),('PyTorch',4,5,True),('Docker',3,3,False)])]
def seed(db):
    if db.query(User).first():
        if not db.query(User).filter_by(email="admin@talentreadiness.demo").first(): db.add(User(name="System Admin",email="admin@talentreadiness.demo",password_hash=hash_password("demo123"),role="admin",job_title="Platform Administrator",department="Operations"))
        
        if not db.query(CoveragePolicy).first(): db.add(CoveragePolicy(coverage_assignment_mode="Consent Required",default_incentive_multiplier=1.5))
        for name,title,dept,email in [("Arjun Patel","ML Engineer","Machine Learning","arjunpatel@talentreadiness.demo"),("Nina Brooks","Data Engineer","Data Engineering","ninabrooks@talentreadiness.demo"),("Lucas Green","Software Engineer","Software Engineering","lucasgreen@talentreadiness.demo")]:
            if not db.query(User).filter_by(email=email).first():
                employee=User(name=name,email=email,password_hash=hash_password("demo123"),role="employee",job_title=title,department=dept)
                db.add(employee); db.flush()
                db.add(Availability(employee_id=employee.id,date=date.today(),status="Available",available_hours=8))
        db.commit(); return
    manager=User(name="Sujal Rao",email="manager@talentreadiness.demo",password_hash=hash_password("demo123"),role="manager",job_title="Engineering Manager",department="AI Engineering"); db.add(manager); db.flush()
    db.add(User(name="System Admin",email="admin@talentreadiness.demo",password_hash=hash_password("demo123"),role="admin",job_title="Platform Administrator",department="Operations"))
    db.add(CoveragePolicy(coverage_assignment_mode="Consent Required",default_incentive_multiplier=1.5))
    skillrows={n:Skill(name=n,category="Data & AI" if n not in ['React','Node.js'] else 'Software') for n in SKILLS}; db.add_all(skillrows.values()); db.flush()
    employees=[]
    for i,(name,title,dept) in enumerate(NAMES):
        u=User(name=name,email=name.lower().replace(' ','')+"@talentreadiness.demo",password_hash=hash_password("demo123"),role="employee",job_title=title,department=dept); db.add(u); db.flush(); employees.append(u)
        relevant = ["Python","SQL","Machine Learning","PyTorch","AWS","Pandas"] if title=="ML Engineer" else ["Python","SQL","Pandas","Scikit-learn","Machine Learning"] if title=="Data Scientist" else ["Python","NLP","RAG","FastAPI","Transformers"] if title=="AI Engineer" else ["Python","SQL","Spark","Kafka","Airflow"] if title=="Data Engineer" else ["React","Node.js","PostgreSQL","Docker","Python"]
        for j,n in enumerate(relevant): db.add(EmployeeSkill(employee_id=u.id,skill_id=skillrows[n].id,proficiency=max(2,5-((i+j)%3)),years_experience=2+(i+j)%6))
        db.add(Availability(employee_id=u.id,date=date.today(),status="Available" if i not in [0,7] else "Partially Available",available_hours=8 if i not in [0,7] else 4))
    # John is absent; Aisha is a clearly excellent fraud replacement.
    john=employees[0]; john.name="John Smith"; john.job_title="ML Engineer"
    john_skills={x.skill_id:x for x in john.skills}
    for n,p in [("Python",5),("PyTorch",5),("SQL",4),("AWS",3),("Machine Learning",5)]:
        current=john_skills.get(skillrows[n].id)
        if current: current.proficiency=p; current.years_experience=5
        else: db.add(EmployeeSkill(employee_id=john.id,skill_id=skillrows[n].id,proficiency=p,years_experience=5))
    aisha_skills={x.skill_id:x for x in employees[5].skills}
    for n,p in [("Python",5),("PyTorch",5),("SQL",4),("AWS",4),("Machine Learning",5)]:
        current=aisha_skills.get(skillrows[n].id)
        if current: current.proficiency=p; current.years_experience=6
        else: db.add(EmployeeSkill(employee_id=employees[5].id,skill_id=skillrows[n].id,proficiency=p,years_experience=6))
    john_availability=db.query(Availability).filter_by(employee_id=john.id,date=date.today()).one()
    john_availability.status="Unavailable"; john_availability.available_hours=0
    for pi,(name,desc,reqs) in enumerate(PROJECTS):
        p=Project(name=name,description=desc,manager_id=manager.id,priority="High" if pi in [0,3,4] else "Medium",status="Active"); db.add(p); db.flush()
        for n,prof,importance,mandatory in reqs: db.add(ProjectSkill(project_id=p.id,skill_id=skillrows[n].id,required_proficiency=prof,importance=importance,mandatory=mandatory))
        for e in employees[pi*3:pi*3+4]: db.add(ProjectMember(project_id=p.id,employee_id=e.id,allocation_percentage=20+((e.id*13)%55)))
    db.flush(); db.add_all([Absence(employee_id=john.id,project_id=1,date=date.today(),reason="Unexpected leave"),Absence(employee_id=employees[7].id,project_id=2,date=date.today(),reason="Medical appointment"),Absence(employee_id=employees[12].id,project_id=5,date=date.today(),reason="Personal leave")]); db.commit()
