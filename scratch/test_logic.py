def test_logic():
    sched_plan = 20
    sched_act = 0
    ls_crsvar = 15
    new_plan = 4
    
    # simulate
    passed_crs = sched_plan - ls_crsvar
    min_allowed_plan = sched_act
    min_allowed_plan = max(min_allowed_plan, passed_crs)
    
    print(f"passed_crs = {passed_crs}")
    print(f"min_allowed_plan = {min_allowed_plan}")
    
    if new_plan < min_allowed_plan:
        print("ERROR: Cannot reduce")
    else:
        print("ACCEPTED")
        
    plan_diff = new_plan - sched_plan
    ls_crsvar += plan_diff
    print(f"new ls_crsvar = {ls_crsvar}")

test_logic()
