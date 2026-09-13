from app.scoring import score_candidate
REQ=[{"name":"Python","required_proficiency":4,"importance":5,"mandatory":True},{"name":"AWS","required_proficiency":3,"importance":3,"mandatory":False}]
def test_excellent_available_candidate_scores_high():
    s=score_candidate(REQ,{"Python":5,"AWS":4},8,8,30,True,2)
    assert s['overall_score'] > 85 and not s['gaps']
def test_missing_mandatory_is_penalized():
    s=score_candidate(REQ,{"AWS":5},8,8,0,True,2)
    assert s['mandatory_missing'] and s['overall_score'] < 55
def test_partial_availability_is_visible():
    s=score_candidate(REQ,{"Python":5,"AWS":4},4,8,20,True,1)
    assert s['availability_score']==50
