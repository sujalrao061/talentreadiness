"""Transparent candidate scoring; isolated for straightforward testing and future matching extensions."""
def score_candidate(requirements, candidate_skills, available_hours, required_hours, workload, role_compatible, project_experience):
    total_weight = sum(r["importance"] * (2 if r["mandatory"] else 1) for r in requirements) or 1
    earned = 0; matches=[]; gaps=[]; mandatory_missing=False
    for r in requirements:
        weight=r["importance"]*(2 if r["mandatory"] else 1); have=candidate_skills.get(r["name"],0)
        ratio=min(have/r["required_proficiency"],1)
        if have == 0: gaps.append(f"Missing: {r['name']}")
        elif have < r["required_proficiency"]: gaps.append(f"{r['name']} is {have}/5 (needs {r['required_proficiency']}/5)")
        else: matches.append(f"Meets {r['name']} requirement")
        if r["mandatory"] and have == 0: mandatory_missing=True
        earned += weight*ratio
    skill=earned/total_weight*100
    availability=min(available_hours/max(required_hours,1),1)*100
    capacity=max(0,100-workload)
    compatibility=min(100, (70 if role_compatible else 40) + min(project_experience,3)*10)
    overall=skill*.50+availability*.20+capacity*.15+compatibility*.15
    if mandatory_missing: overall *= .55
    return {"overall_score":round(overall,1),"skill_match":round(skill,1),"availability_score":round(availability,1),"workload_capacity":round(capacity,1),"project_compatibility":round(compatibility,1),"matches":matches,"gaps":gaps,"mandatory_missing":mandatory_missing}
