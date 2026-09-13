from datetime import date, datetime
from typing import Literal
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from .database import Base, engine, get_db
from .models import *
from .auth import *
from .seed import seed
from .scoring import score_candidate

app=FastAPI(title="TalentReadiness API")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
@app.on_event("startup")
def startup(): Base.metadata.create_all(engine); db=next(get_db()); seed(db); db.close()
@app.get("/health")
def health(): return {"status":"ok"}
class Signup(BaseModel): name:str; email:EmailStr; password:str=Field(min_length=6); role:Literal['employee','manager']='employee'; work_id:str=''; job_title:str=''; department:str=''
class Login(BaseModel): email:EmailStr; password:str
class AvailabilityIn(BaseModel): date:date; status:Literal['Available','Remote','Unavailable','Partially Available']; available_hours:float=Field(ge=0,le=24)
class AbsenceIn(BaseModel): employee_id:int; project_id:int; date:date; reason:str=''
class FindIn(BaseModel): absent_employee_id:int; project_id:int; date:date; required_hours:float=Field(default=8,gt=0,le=24)
class AssignIn(BaseModel): absent_employee_id:int; replacement_employee_id:int; date:date; required_hours:float=Field(default=8,gt=0,le=24); incentive_multiplier:float|None=Field(default=None,ge=1,le=5); reason:str=''
class CoverageRequestIn(BaseModel): absent_employee_id:int; requested_employee_id:int; date:date; required_hours:float=Field(default=8,gt=0,le=24); incentive_multiplier:float=Field(default=1.5,ge=1,le=5); reason:str=''
class CoverageSettingsIn(BaseModel): coverage_assignment_mode:Literal['Consent Required','Direct Assignment']; default_incentive_multiplier:float=Field(ge=1,le=5)
class ProjectIn(BaseModel): name:str; description:str=''; priority:str='Medium'; status:str='Active'
class ProjectSkillIn(BaseModel): skill_id:int; required_proficiency:int=Field(ge=1,le=5); importance:int=Field(ge=1,le=5); mandatory:bool=False
class MemberIn(BaseModel): employee_id:int; allocation_percentage:int=Field(ge=0,le=100)
class ReassignMemberIn(BaseModel): current_employee_id:int; replacement_employee_id:int; allocation_percentage:int=Field(default=20,ge=0,le=100)
class EmployeeSkillIn(BaseModel): skill_id:int; proficiency:int=Field(ge=1,le=5); years_experience:float=Field(ge=0,le=60)
class EmployeeCreate(BaseModel):
    name:str
    email:EmailStr
    job_title:str
    department:str
    password:str=Field(default="welcome123",min_length=6)
class ProfileIn(BaseModel): name:str=Field(min_length=1,max_length=120); job_title:str=Field(max_length=120); department:str=Field(max_length=120)
def user_out(u): return {"id":u.id,"name":u.name,"email":u.email,"role":u.role,"job_title":u.job_title,"department":u.department}
@app.post('/auth/signup')
def signup(body:Signup,db:Session=Depends(get_db)):
    if db.query(User).filter_by(email=body.email).first(): raise HTTPException(400,'Email already registered')
    if body.work_id.upper().startswith('MGR-'): body.role='manager'
    elif body.work_id.upper().startswith('EMP-'): body.role='employee'
    elif body.work_id: raise HTTPException(400,'Work ID must start with MGR- or EMP-')
    u=User(**body.model_dump(exclude={'password'}),password_hash=hash_password(body.password)); db.add(u);db.commit();db.refresh(u);return {"access_token":create_token(u),"user":user_out(u)}
@app.post('/auth/login')
def login(body:Login,db:Session=Depends(get_db)):
    u=db.query(User).filter_by(email=body.email).first()
    if not u or not verify_password(body.password,u.password_hash): raise HTTPException(401,'Incorrect email or password')
    return {"access_token":create_token(u),"user":user_out(u)}
@app.get('/auth/me')
def me(u:User=Depends(current_user)): return user_out(u)
@app.get('/skills')
def skills(_:User=Depends(current_user),db:Session=Depends(get_db)): return [{"id":s.id,"name":s.name,"category":s.category} for s in db.query(Skill).order_by(Skill.name)]
@app.get('/employees')
def employees(department:str|None=None,role:str|None=None,availability:str|None=None,_:User=Depends(manager_required),db:Session=Depends(get_db)):
    q=db.query(User).filter_by(role='employee')
    if department:q=q.filter(User.department==department)
    if role:q=q.filter(User.job_title==role)
    result=[]
    for u in q.options(joinedload(User.skills).joinedload(EmployeeSkill.skill)):
        av=db.query(Availability).filter_by(employee_id=u.id,date=date.today()).first(); workload=sum(x.allocation_percentage for x in db.query(ProjectMember).filter_by(employee_id=u.id))
        if availability and (not av or av.status!=availability): continue
        result.append({**user_out(u),"top_skills":[{"name":x.skill.name,"proficiency":x.proficiency} for x in sorted(u.skills,key=lambda x:x.proficiency,reverse=True)[:4]],"availability":av.status if av else 'Unknown',"available_hours":av.available_hours if av else 0,"workload":workload})
    return result
@app.post('/employees')
def create_employee(body:EmployeeCreate,_:User=Depends(manager_required),db:Session=Depends(get_db)):
    if db.query(User).filter_by(email=body.email).first(): raise HTTPException(400,'Email already registered')
    employee=User(name=body.name,email=body.email,password_hash=hash_password(body.password),role='employee',job_title=body.job_title,department=body.department)
    db.add(employee); db.commit(); db.refresh(employee)
    return user_out(employee)
@app.get('/employees/{employee_id}')
def employee(employee_id:int,current:User=Depends(current_user),db:Session=Depends(get_db)):
    if current.role != 'manager' and current.id != employee_id: raise HTTPException(403,'You can only view your own profile')
    u=db.query(User).options(joinedload(User.skills).joinedload(EmployeeSkill.skill)).get(employee_id)
    if not u: raise HTTPException(404,'Employee not found')
    return {**user_out(u),"skills":[{"id":x.skill_id,"name":x.skill.name,"proficiency":x.proficiency,"years_experience":x.years_experience} for x in u.skills]}
@app.put('/employees/{employee_id}/profile')
def update_profile(employee_id:int,body:ProfileIn,current:User=Depends(current_user),db:Session=Depends(get_db)):
    if current.role != 'manager' and current.id != employee_id: raise HTTPException(403,'You can only update your own profile')
    employee=db.get(User,employee_id)
    if not employee: raise HTTPException(404,'Employee not found')
    for key,value in body.model_dump().items(): setattr(employee,key,value)
    db.commit(); return user_out(employee)
@app.put('/employees/{employee_id}/skills')
def save_employee_skill(employee_id:int,body:EmployeeSkillIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
    if u.id != employee_id and u.role != 'manager': raise HTTPException(403,'You can only update your own skills')
    row=db.query(EmployeeSkill).filter_by(employee_id=employee_id,skill_id=body.skill_id).first()
    if not row: row=EmployeeSkill(employee_id=employee_id,**body.model_dump()); db.add(row)
    else:
        row.proficiency=body.proficiency; row.years_experience=body.years_experience
    db.commit(); return {"ok":True}
@app.put('/availability')
def set_availability(body:AvailabilityIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
    av=db.query(Availability).filter_by(employee_id=u.id,date=body.date).first()
    if not av: av=Availability(employee_id=u.id,**body.model_dump());db.add(av)
    else:
        for k,v in body.model_dump().items():setattr(av,k,v)
    db.commit();return {"ok":True}
@app.put('/employees/{employee_id}/availability')
def manager_set_availability(employee_id:int,body:AvailabilityIn,_:User=Depends(manager_required),db:Session=Depends(get_db)):
    if not db.get(User,employee_id): raise HTTPException(404,'Employee not found')
    av=db.query(Availability).filter_by(employee_id=employee_id,date=body.date).first()
    if not av:
        av=Availability(employee_id=employee_id,**body.model_dump())
        db.add(av)
    else:
        av.status=body.status
        av.available_hours=body.available_hours
    existing=db.query(Absence).filter_by(employee_id=employee_id,date=body.date).first()
    if body.status == 'Unavailable':
        # Make a manual full-day unavailability visible in the dashboard.
        # The first active assignment gives the manager a replacement context.
        membership=db.query(ProjectMember).filter_by(employee_id=employee_id).first()
        if not existing and membership:
            db.add(Absence(employee_id=employee_id,project_id=membership.project_id,date=body.date,reason='Marked unavailable from employee directory'))
    else:
        # Available and partial capacity both resolve a full-day absence.
        db.query(Absence).filter_by(employee_id=employee_id,date=body.date).delete()
    db.commit()
    return {"ok":True}
@app.get('/projects')
def projects(_:User=Depends(current_user),db:Session=Depends(get_db)): return [{"id":p.id,"name":p.name,"description":p.description,"priority":p.priority,"status":p.status,"member_count":len(p.members)} for p in db.query(Project).options(joinedload(Project.members))]
@app.post('/projects')
def create_project(body:ProjectIn,u:User=Depends(manager_required),db:Session=Depends(get_db)): p=Project(**body.model_dump(),manager_id=u.id);db.add(p);db.commit();db.refresh(p);return {"id":p.id}
@app.put('/projects/{project_id}')
def edit_project(project_id:int,body:ProjectIn,_:User=Depends(manager_required),db:Session=Depends(get_db)):
    p=db.get(Project,project_id)
    if not p: raise HTTPException(404,'Project not found')
    for k,v in body.model_dump().items(): setattr(p,k,v)
    db.commit(); return {"ok":True}
@app.get('/projects/{project_id}')
def project(project_id:int,_:User=Depends(current_user),db:Session=Depends(get_db)):
    p=db.query(Project).options(joinedload(Project.skills).joinedload(ProjectSkill.skill),joinedload(Project.members).joinedload(ProjectMember.employee)).get(project_id)
    if not p:raise HTTPException(404,'Project not found')
    return {"id":p.id,"name":p.name,"description":p.description,"priority":p.priority,"status":p.status,"skills":[{"skill_id":x.skill_id,"name":x.skill.name,"required_proficiency":x.required_proficiency,"importance":x.importance,"mandatory":x.mandatory} for x in p.skills],"members":[{"id":x.employee.id,"name":x.employee.name,"role":x.employee.job_title,"allocation":x.allocation_percentage} for x in p.members]}
@app.post('/projects/{project_id}/skills')
def add_project_skill(project_id:int,body:ProjectSkillIn,_:User=Depends(manager_required),db:Session=Depends(get_db)):
    if not db.get(Project,project_id) or not db.get(Skill,body.skill_id): raise HTTPException(404,'Project or skill not found')
    if db.query(ProjectSkill).filter_by(project_id=project_id,skill_id=body.skill_id).first(): raise HTTPException(400,'Skill already required for this project')
    db.add(ProjectSkill(project_id=project_id,**body.model_dump()));db.commit();return {"ok":True}
@app.post('/projects/{project_id}/members')
def add_member(project_id:int,body:MemberIn,_:User=Depends(manager_required),db:Session=Depends(get_db)):
    if not db.get(Project,project_id) or not db.get(User,body.employee_id): raise HTTPException(404,'Project or employee not found')
    if db.query(ProjectMember).filter_by(project_id=project_id,employee_id=body.employee_id).first(): raise HTTPException(400,'Employee is already a project member')
    db.add(ProjectMember(project_id=project_id,**body.model_dump()));db.commit();return {"ok":True}
@app.put('/projects/{project_id}/reassign')
def reassign_project_member(project_id:int,body:ReassignMemberIn,_:User=Depends(manager_required),db:Session=Depends(get_db)):
    if body.current_employee_id==body.replacement_employee_id: raise HTTPException(400,'Choose a different replacement employee')
    current=db.query(ProjectMember).filter_by(project_id=project_id,employee_id=body.current_employee_id).first()
    replacement=db.get(User,body.replacement_employee_id)
    if not current or not replacement or replacement.role!='employee': raise HTTPException(404,'Project member or replacement employee not found')
    next_member=db.query(ProjectMember).filter_by(project_id=project_id,employee_id=body.replacement_employee_id).first()
    if next_member: next_member.allocation_percentage=body.allocation_percentage
    else: db.add(ProjectMember(project_id=project_id,employee_id=body.replacement_employee_id,allocation_percentage=body.allocation_percentage))
    db.delete(current); db.commit()
    return {"message":"Project member reassigned successfully"}
@app.delete('/projects/{project_id}/members/{employee_id}')
def remove_member(project_id:int,employee_id:int,_:User=Depends(manager_required),db:Session=Depends(get_db)):
    row=db.query(ProjectMember).filter_by(project_id=project_id,employee_id=employee_id).first()
    if not row: raise HTTPException(404,'Project member not found')
    db.delete(row);db.commit();return {"ok":True}
@app.get('/absences')
def absences(_:User=Depends(manager_required),db:Session=Depends(get_db)): return [{"id":a.id,"employee_id":a.employee_id,"employee":a.employee.name,"role":a.employee.job_title,"project_id":a.project_id,"project":a.project.name,"date":str(a.date),"reason":a.reason} for a in db.query(Absence).options(joinedload(Absence.employee),joinedload(Absence.project)).order_by(Absence.date.desc())]
@app.post('/absences')
def absence(body:AbsenceIn,_:User=Depends(manager_required),db:Session=Depends(get_db)):
    if not db.get(User,body.employee_id) or not db.get(Project,body.project_id): raise HTTPException(404,'Employee or project not found')
    if not db.query(ProjectMember).filter_by(project_id=body.project_id,employee_id=body.employee_id).first(): raise HTTPException(400,'Employee is not a member of the selected project')
    if db.query(Absence).filter_by(employee_id=body.employee_id,project_id=body.project_id,date=body.date).first(): raise HTTPException(400,'This absence already exists')
    a=Absence(**body.model_dump());db.add(a)
    availability=db.query(Availability).filter_by(employee_id=body.employee_id,date=body.date).first()
    if not availability:
        availability=Availability(employee_id=body.employee_id,date=body.date,status='Unavailable',available_hours=0);db.add(availability)
    else:
        availability.status='Unavailable'; availability.available_hours=0
    db.commit();return {"id":a.id}
@app.delete('/absences/{absence_id}')
def resolve_absence(absence_id:int,_:User=Depends(manager_required),db:Session=Depends(get_db)):
    absence=db.get(Absence,absence_id)
    if not absence: raise HTTPException(404,'Absence not found')
    availability=db.query(Availability).filter_by(employee_id=absence.employee_id,date=absence.date).first()
    if availability:
        availability.status='Available'; availability.available_hours=8
    db.delete(absence);db.commit();return {"ok":True,"message":"Employee marked as returned and available"}
@app.post('/replacement/find')
def find(body:FindIn,_:User=Depends(manager_required),db:Session=Depends(get_db)):
    project=db.query(Project).options(joinedload(Project.skills).joinedload(ProjectSkill.skill)).get(body.project_id); absent=db.get(User,body.absent_employee_id)
    if not project or not absent: raise HTTPException(404,'Project or absent employee not found')
    if not db.query(ProjectMember).filter_by(project_id=project.id,employee_id=absent.id).first(): raise HTTPException(400,'Absent employee is not assigned to this project')
    req=[{"name":x.skill.name,"required_proficiency":x.required_proficiency,"importance":x.importance,"mandatory":x.mandatory} for x in project.skills]; candidates=[]
    for u in db.query(User).options(joinedload(User.skills).joinedload(EmployeeSkill.skill)).filter(User.role=='employee',User.id!=absent.id):
        # An explicit record for the requested day wins. Otherwise use the
        # employee's latest declared availability as the working baseline,
        # which keeps the demo useful across calendar days.
        av=db.query(Availability).filter_by(employee_id=u.id,date=body.date).first()
        if not av:
            av=db.query(Availability).filter(Availability.employee_id==u.id, Availability.date<=body.date).order_by(Availability.date.desc()).first()
        if not av or av.status=='Unavailable':continue
        workload=sum(x.allocation_percentage for x in db.query(ProjectMember).filter_by(employee_id=u.id)); es={x.skill.name:x.proficiency for x in u.skills}; experience=db.query(ProjectMember).filter_by(employee_id=u.id).count()
        scoring=score_candidate(req,es,av.available_hours,body.required_hours,workload,u.job_title==absent.job_title,experience)
        candidates.append({**user_out(u),**scoring,"available_hours":av.available_hours,"availability_status":av.status,"workload":workload,"skills":es})
    candidates.sort(key=lambda x:(x['overall_score'],x['availability_score'],x['workload_capacity'],x['project_compatibility']),reverse=True)
    qualified=[x for x in candidates if not x['mandatory_missing']]
    # A manager still needs a decision aid when there is a skills shortage.
    # Return the highest-ranked partial matches (heavily penalized by scoring)
    # and let the UI expose each missing mandatory skill for review.
    ranked = qualified or candidates
    return {"project":project.name,"absent_employee":absent.name,"required_hours":body.required_hours,"candidates":ranked[:5],"message":None if ranked else 'No suitable replacement found. No employees are available on the selected date.',"partial_matches":not bool(qualified)}
def policy(db): return db.query(CoveragePolicy).first() or CoveragePolicy(coverage_assignment_mode='Consent Required',default_incentive_multiplier=1.5)
@app.get('/coverage-policy')
def coverage_policy(_:User=Depends(current_user),db:Session=Depends(get_db)):
    p=policy(db); return {"coverage_assignment_mode":p.coverage_assignment_mode,"default_incentive_multiplier":p.default_incentive_multiplier}
def create_assignment(db,project_id,absent_id,replacement_id,when,actor,mode,multiplier,hours,reason=''):
    existing=db.query(ReplacementAssignment).filter_by(project_id=project_id,absent_employee_id=absent_id,date=when).first()
    if existing: existing.replacement_employee_id=replacement_id
    else:
        existing=ReplacementAssignment(project_id=project_id,absent_employee_id=absent_id,replacement_employee_id=replacement_id,date=when,assigned_by=actor.id); db.add(existing)
    if not db.query(ProjectMember).filter_by(project_id=project_id,employee_id=replacement_id).first(): db.add(ProjectMember(project_id=project_id,employee_id=replacement_id,allocation_percentage=20))
    db.add(CoverageAuditLog(project_id=project_id,absent_employee_id=absent_id,replacement_employee_id=replacement_id,assignment_mode=mode,incentive_multiplier=multiplier,required_hours=hours,performed_by=actor.id,reason=reason))
    db.commit(); return existing
@app.post('/replacement/{project_id}/assign')
def assign(project_id:int,body:AssignIn,u:User=Depends(manager_required),db:Session=Depends(get_db)):
    if body.replacement_employee_id==body.absent_employee_id: raise HTTPException(400,'Replacement must be a different employee')
    if not db.get(Project,project_id) or not db.get(User,body.absent_employee_id) or not db.get(User,body.replacement_employee_id): raise HTTPException(404,'Project or employee not found')
    if not db.query(Absence).filter_by(project_id=project_id,employee_id=body.absent_employee_id,date=body.date).first(): raise HTTPException(400,'Record an absence before assigning a replacement')
    current=policy(db)
    if current.coverage_assignment_mode=='Consent Required':
        multiplier=body.incentive_multiplier or current.default_incentive_multiplier
        request=CoverageRequest(project_id=project_id,absent_employee_id=body.absent_employee_id,requested_employee_id=body.replacement_employee_id,date=body.date,required_hours=body.required_hours,incentive_multiplier=multiplier,status='Pending',requested_by=u.id); db.add(request)
        db.add(CoverageAuditLog(project_id=project_id,absent_employee_id=body.absent_employee_id,replacement_employee_id=body.replacement_employee_id,assignment_mode='Consent Required',incentive_multiplier=multiplier,required_hours=body.required_hours,performed_by=u.id,reason=body.reason or 'Coverage request sent'))
        db.commit(); return {"id":request.id,"message":"Coverage request sent. Waiting for employee acceptance."}
    assignment=create_assignment(db,project_id,body.absent_employee_id,body.replacement_employee_id,body.date,u,'Direct Assignment',body.incentive_multiplier or current.default_incentive_multiplier,body.required_hours,body.reason or 'Manager direct assignment')
    return {"id":assignment.id,"message":"Temporary replacement assigned successfully"}
@app.post('/projects/{project_id}/coverage-requests')
def project_coverage_request(project_id:int,body:CoverageRequestIn,u:User=Depends(manager_required),db:Session=Depends(get_db)):
    if not db.query(Absence).filter_by(project_id=project_id,employee_id=body.absent_employee_id,date=body.date).first(): raise HTTPException(400,'Record an absence before requesting coverage')
    if not db.get(User,body.requested_employee_id): raise HTTPException(404,'Employee not found')
    request=CoverageRequest(project_id=project_id,absent_employee_id=body.absent_employee_id,requested_employee_id=body.requested_employee_id,date=body.date,required_hours=body.required_hours,incentive_multiplier=body.incentive_multiplier,status='Pending',requested_by=u.id); db.add(request); db.commit(); return {"id":request.id,"message":"Coverage request sent"}
@app.get('/coverage-requests/mine')
def my_coverage_requests(u:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(CoverageRequest).options(joinedload(CoverageRequest.project),joinedload(CoverageRequest.absent_employee),joinedload(CoverageRequest.manager)).filter_by(requested_employee_id=u.id).order_by(CoverageRequest.created_at.desc()).all()
    return [{"id":r.id,"project":r.project.name,"absent_employee":r.absent_employee.name,"manager":r.manager.name,"date":str(r.date),"required_hours":r.required_hours,"incentive_multiplier":r.incentive_multiplier,"status":r.status} for r in rows]
@app.get('/coverage-requests')
def coverage_requests(_:User=Depends(manager_required),db:Session=Depends(get_db)):
    rows=db.query(CoverageRequest).options(joinedload(CoverageRequest.project),joinedload(CoverageRequest.absent_employee),joinedload(CoverageRequest.requested_employee)).order_by(CoverageRequest.created_at.desc()).all()
    return [{"id":r.id,"project":r.project.name,"absent_employee":r.absent_employee.name,"replacement_employee":r.requested_employee.name,"date":str(r.date),"required_hours":r.required_hours,"incentive_multiplier":r.incentive_multiplier,"status":r.status,"created_at":str(r.created_at)} for r in rows]
@app.get('/coverage-assignments/mine')
def my_coverage_assignments(u:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(ReplacementAssignment).filter_by(replacement_employee_id=u.id).order_by(ReplacementAssignment.date.desc()).all(); out=[]
    for r in rows:
        audit=db.query(CoverageAuditLog).filter_by(project_id=r.project_id,absent_employee_id=r.absent_employee_id,replacement_employee_id=u.id).order_by(CoverageAuditLog.created_at.desc()).first()
        project=db.get(Project,r.project_id); absent=db.get(User,r.absent_employee_id); manager=db.get(User,r.assigned_by)
        out.append({"id":r.id,"project":project.name,"absent_employee":absent.name,"manager":manager.name,"date":str(r.date),"required_hours":audit.required_hours if audit else 8,"incentive_multiplier":audit.incentive_multiplier if audit else 1.5,"assignment_mode":audit.assignment_mode if audit else 'Direct Assignment'})
    return out
@app.post('/coverage-requests/{request_id}/accept')
def accept_coverage_request(request_id:int,u:User=Depends(current_user),db:Session=Depends(get_db)):
    r=db.get(CoverageRequest,request_id)
    if not r: raise HTTPException(404,'Coverage request not found')
    if r.requested_employee_id!=u.id: raise HTTPException(403,'You can only respond to your own coverage request')
    if r.status!='Pending': return {"id":r.id,"message":f'This request is already {r.status.lower()}'}
    av=db.query(Availability).filter_by(employee_id=u.id,date=r.date).first()
    if not av or av.status=='Unavailable' or av.available_hours<r.required_hours: raise HTTPException(400,'You are no longer available for the requested hours')
    r.status='Accepted'; r.responded_at=datetime.utcnow(); create_assignment(db,r.project_id,r.absent_employee_id,u.id,r.date,u,'Consent Required',r.incentive_multiplier,r.required_hours,'Employee accepted coverage request'); return {"id":r.id,"message":"Coverage accepted and assignment confirmed"}
@app.post('/coverage-requests/{request_id}/decline')
def decline_coverage_request(request_id:int,u:User=Depends(current_user),db:Session=Depends(get_db)):
    r=db.get(CoverageRequest,request_id)
    if not r: raise HTTPException(404,'Coverage request not found')
    if r.requested_employee_id!=u.id: raise HTTPException(403,'You can only respond to your own coverage request')
    if r.status!='Pending': return {"id":r.id,"message":f'This request is already {r.status.lower()}'}
    r.status='Declined'; r.responded_at=datetime.utcnow(); db.add(CoverageAuditLog(project_id=r.project_id,absent_employee_id=r.absent_employee_id,replacement_employee_id=u.id,assignment_mode='Consent Required',incentive_multiplier=r.incentive_multiplier,required_hours=r.required_hours,performed_by=u.id,reason='Employee declined coverage request')); db.commit(); return {"id":r.id,"message":"Coverage request declined"}
@app.get('/admin/settings')
def admin_settings(_:User=Depends(admin_required),db:Session=Depends(get_db)):
    p=policy(db); return {"coverage_assignment_mode":p.coverage_assignment_mode,"default_incentive_multiplier":p.default_incentive_multiplier}
@app.put('/admin/settings')
def save_admin_settings(body:CoverageSettingsIn,u:User=Depends(admin_required),db:Session=Depends(get_db)):
    p=policy(db)
    if not p.id: db.add(p)
    p.coverage_assignment_mode=body.coverage_assignment_mode; p.default_incentive_multiplier=body.default_incentive_multiplier; p.updated_by=u.id; db.commit(); return {"message":"Coverage policy saved","coverage_assignment_mode":p.coverage_assignment_mode,"default_incentive_multiplier":p.default_incentive_multiplier}
@app.get('/admin/audit-log')
def audit_log(_:User=Depends(admin_required),db:Session=Depends(get_db)):
    rows=db.query(CoverageAuditLog).options(joinedload(CoverageAuditLog.project),joinedload(CoverageAuditLog.absent_employee),joinedload(CoverageAuditLog.replacement_employee)).order_by(CoverageAuditLog.created_at.desc()).limit(30).all()
    return [{"id":r.id,"project":r.project.name,"absent_employee":r.absent_employee.name,"replacement_employee":r.replacement_employee.name,"assignment_mode":r.assignment_mode,"incentive_multiplier":r.incentive_multiplier,"required_hours":r.required_hours,"reason":r.reason,"created_at":str(r.created_at)} for r in rows]
@app.get('/dashboard/manager')
def manager_dashboard(_:User=Depends(manager_required),db:Session=Depends(get_db)):
    today=date.today(); abs_=db.query(Absence).options(joinedload(Absence.employee),joinedload(Absence.project)).filter_by(date=today).all()
    absent_ids={a.employee_id for a in abs_}
    available_today=0
    working_today=[]
    remote_today=[]
    for employee in db.query(User).filter_by(role='employee'):
        availability=db.query(Availability).filter_by(employee_id=employee.id,date=today).first()
        if employee.id not in absent_ids and availability and availability.status != 'Unavailable':
            available_today += 1
            person={"id":employee.id,"name":employee.name,"role":employee.job_title,"status":availability.status,"hours":availability.available_hours}
            if availability.status == 'Remote': remote_today.append(person)
            else: working_today.append(person)
    risks=[]
    for project in db.query(Project).options(joinedload(Project.skills).joinedload(ProjectSkill.skill)).filter_by(status='Active'):
        for requirement in project.skills:
            if not requirement.mandatory: continue
            covered=0
            for skill in db.query(EmployeeSkill).filter_by(skill_id=requirement.skill_id):
                av=db.query(Availability).filter_by(employee_id=skill.employee_id,date=today).first()
                if skill.proficiency >= requirement.required_proficiency and skill.employee_id not in absent_ids and av and av.status != 'Unavailable': covered += 1
            if covered <= 1:
                risks.append({"project":project.name,"level":"HIGH","reason":f"Only {covered} available employee currently has the required {requirement.skill.name} skill."}); break
    absence_items=[]
    for absence in abs_:
        assignment=db.query(ReplacementAssignment).filter_by(project_id=absence.project_id,absent_employee_id=absence.employee_id,date=absence.date).first()
        replacement=db.get(User,assignment.replacement_employee_id) if assignment else None
        absence_items.append({"id":absence.id,"employee_id":absence.employee_id,"employee":absence.employee.name,"role":absence.employee.job_title,"project_id":absence.project_id,"project":absence.project.name,"date":str(absence.date),"reason":absence.reason,"replacement":replacement.name if replacement else None})
    return {"total_employees":db.query(User).filter_by(role='employee').count(),"active_projects":db.query(Project).filter_by(status='Active').count(),"available_today":available_today,"absent_today":len(abs_),"working_today":working_today,"remote_today":remote_today,"absences":absence_items,"staffing_risks":risks[:3]}
@app.get('/dashboard/employee')
def employee_dashboard(u:User=Depends(current_user),db:Session=Depends(get_db)):
    skills=db.query(EmployeeSkill).options(joinedload(EmployeeSkill.skill)).filter_by(employee_id=u.id).all(); members=db.query(ProjectMember).options(joinedload(ProjectMember.project)).filter_by(employee_id=u.id).all(); av=db.query(Availability).filter_by(employee_id=u.id,date=date.today()).first()
    return {"user":user_out(u),"skills":[{"name":s.skill.name,"proficiency":s.proficiency} for s in skills],"projects":[{"name":m.project.name,"allocation":m.allocation_percentage,"status":m.project.status} for m in members],"availability":{"status":av.status,"hours":av.available_hours} if av else None,"readiness_score":round(sum(s.proficiency for s in skills)/max(len(skills),1)*20)}
