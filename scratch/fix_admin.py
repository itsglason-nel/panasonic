        linestat = LineStat.query.filter_by(lineno=lineno).first()
        active_model_codes = set()
        
        if linestat and linestat.active_date == ghost_date:
            if linestat.crsvar and linestat.crsvar > 0:
                active_model_codes.add(linestat.crsmodelcode)
            if linestat.attvar and linestat.attvar > 0:
                active_model_codes.add(linestat.attmodelcode)
            if linestat.gmsvar and linestat.gmsvar > 0:
                active_model_codes.add(linestat.gmsmodelcode)
            if linestat.invar and linestat.invar > 0:
                active_model_codes.add(linestat.inmodelcode)
            if linestat.outvar and linestat.outvar > 0:
                active_model_codes.add(linestat.outmodelcode)
            if linestat.wcivar and linestat.wcivar > 0:
                active_model_codes.add(linestat.wcimodelcode)
            if linestat.ritvar and linestat.ritvar > 0:
                active_model_codes.add(linestat.ritmodelcode)
            if linestat.fitvar and linestat.fitvar > 0:
                active_model_codes.add(linestat.fitmodelcode)
            if linestat.pitvar and linestat.pitvar > 0:
                active_model_codes.add(linestat.pitmodelcode)
                
        # Get next sequence number for today
        last_sched = WorkSched.query.filter_by(lineno=lineno, date=today_date).order_by(WorkSched.seq.desc()).first()
        next_seq = 0 if not last_sched else last_sched.seq + 1

        for sched in unfinished_scheds:
            if sched.modelcode not in active_model_codes:
                # Unstarted schedule
                if str(sched.id) in unstarted_plans:
                    # User checked it -> create new schedule for today
                    
                    new_plan_val = sched.plan
                    try:
                        if unstarted_plans[str(sched.id)]:
                            new_plan_val = int(unstarted_plans[str(sched.id)])
                    except ValueError:
                        pass
                    
                    # Fix 4: Check for existing today-schedule to avoid UniqueConstraint crash
                    existing = WorkSched.query.filter_by(lineno=lineno, date=today_date, modelcode=sched.modelcode).first()
                    if existing:
                        existing.plan += new_plan_val
                    else:
                        new_sched = WorkSched(
                            lineno=lineno,
                            seq=next_seq,
                            modelcode=sched.modelcode,
                            plan=new_plan_val,
                            act=0,
                            takttime=sched.takttime,
                            date=today_date
                        )
                        db.session.add(new_sched)
                        next_seq += 1
                
                # Close out yesterday's schedule
                sched.plan = sched.act
                
            else:
                # Active model on the conveyor
                if action == 'clear':
                    # Discard & Clear
                    sched.plan = sched.act
                elif action == 'continue':
                    max_var = 0
                    if linestat.crsmodelcode == sched.modelcode and linestat.crsvar:
                        max_var = max(max_var, linestat.crsvar)
                    if linestat.attmodelcode == sched.modelcode and linestat.attvar:
                        max_var = max(max_var, linestat.attvar)
                    if linestat.gmsmodelcode == sched.modelcode and linestat.gmsvar:
                        max_var = max(max_var, linestat.gmsvar)
                    if linestat.inmodelcode == sched.modelcode and linestat.invar:
                        max_var = max(max_var, linestat.invar)
                    if linestat.outmodelcode == sched.modelcode and linestat.outvar:
                        max_var = max(max_var, linestat.outvar)
                        
                    final_plan = max_var
                    
                    # If they updated the plan for the CRS model, check if it's higher
                    if linestat.crsmodelcode == sched.modelcode and crs_new_plan:
                        try:
                            crs_plan_val = int(crs_new_plan)
                            if crs_plan_val > final_plan:
                                final_plan = crs_plan_val
                        except ValueError:
                            pass
                    
                    if final_plan > 0:
                        # Fix 4: Check for existing today-schedule to avoid UniqueConstraint crash
                        existing = WorkSched.query.filter_by(lineno=lineno, date=today_date, modelcode=sched.modelcode).first()
                        if existing:
                            existing.plan += final_plan
                        else:
                            new_sched = WorkSched(
                                lineno=lineno,
                                seq=next_seq,
                                modelcode=sched.modelcode,
                                plan=final_plan,
                                act=0, 
                                takttime=sched.takttime,
                                date=today_date
                            )
                            db.session.add(new_sched)
                            next_seq += 1
                        
                    sched.plan = sched.act

        if action == 'clear':
            if linestat:
                from datetime import datetime
                linestat.status = 'No Work'
                linestat.active_date = None
                linestat.crsmodelcode = None
                linestat.crsvar = 0
                linestat.attmodelcode = None
                linestat.attvar = 0
                linestat.gmsmodelcode = None
                linestat.gmsvar = 0
                linestat.inmodelcode = None
                linestat.invar = 0
                linestat.inunique = None
                linestat.inpart1mod = None
                linestat.inpart1desc = None
                linestat.inpart2mod = None
                linestat.inpart2desc = None
                linestat.inpart3mod = None
                linestat.inpart3desc = None
                linestat.inpart4mod = None
                linestat.inpart4desc = None
                linestat.inpart5mod = None
                linestat.inpart5desc = None
                linestat.inpart6mod = None
                linestat.inpart6desc = None
                linestat.outmodelcode = None
                linestat.outvar = 0
                linestat.outpart1mod = None
                linestat.outpart1desc = None
                linestat.outpart2mod = None
                linestat.outpart2desc = None
                linestat.outpart3mod = None
                linestat.outpart3desc = None
                linestat.compmod = None
                linestat.fan1mod = None
                linestat.fan2mod = None
                linestat.crspart1mod = None
                linestat.crspart1desc = None
                linestat.crspart2mod = None
                linestat.crspart2desc = None
                linestat.crspart3mod = None
                linestat.crspart3desc = None
                linestat.crspart4mod = None
                linestat.crspart4desc = None
                linestat.area = None
                linestat.serialstart = None
                linestat.gascharge = 0
                linestat.gmstolpos = 0
                linestat.gmstolneg = 0
                linestat.outmodel = None
                linestat.wcimodelcode = None
                linestat.wcivar = 0
                linestat.ritmodelcode = None
                linestat.ritvar = 0
                linestat.ritprogh = None
                linestat.ritprogf = None
                linestat.ritdata1 = None
                linestat.ritdata1tolpos = None
                linestat.ritdata1tolneg = None
                linestat.ritdata2 = None
                linestat.ritdata2tolpos = None
                linestat.ritdata2tolneg = None
                linestat.ritdata3 = None
                linestat.ritdata3tolpos = None
                linestat.ritdata3tolneg = None
                linestat.ritheat1 = None
                linestat.ritheat2 = None
                linestat.fitmodelcode = None
                linestat.fitvar = 0
                linestat.fitdata1 = None
                linestat.fitdata1tolpos = None
                linestat.fitdata1tolneg = None
                linestat.fitdata2 = None
                linestat.fitdata2tolpos = None
                linestat.fitdata2tolneg = None
                linestat.pitmodelcode = None
                linestat.pitvar = 0
                linestat.pittws = None
                linestat.updtime = datetime.now()
        elif action == 'continue':
            # Fix 3: Transition linestat.active_date to today so the SP's sequence
            # lookup finds today's newly created schedules instead of yesterday's.
            if linestat:
                from datetime import datetime
                linestat.active_date = today_date
                linestat.updtime = datetime.now()
