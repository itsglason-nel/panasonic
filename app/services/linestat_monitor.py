from app.models import db
from app.models.linestat import LineStat
from sqlalchemy import text
from datetime import datetime

def get_current_linestat():
    """Retrieve the single memory block row for LineStat."""
    stat = LineStat.query.get(1)
    if not stat:
        stat = LineStat(id=1, status='No Work')
        db.session.add(stat)
        db.session.commit()
    return stat

def initialize_line(lineno):
    """Initializes the line for the start of the day with Seq 0."""
    try:
        # We just call the Stored Procedure with p_current_model = NULL 
        # to find the very first sequence and load it.
        db.session.execute(
            text("CALL sp_linestat_shift_sequence('crs', :lineno, NULL)"),
            {'lineno': lineno}
        )
        db.session.execute(
            text("CALL sp_linestat_shift_sequence('att', :lineno, NULL)"),
            {'lineno': lineno}
        )
        db.session.execute(
            text("CALL sp_linestat_shift_sequence('gms', :lineno, NULL)"),
            {'lineno': lineno}
        )
        db.session.execute(
            text("CALL sp_linestat_shift_sequence('spamsi', :lineno, NULL)"),
            {'lineno': lineno}
        )
        db.session.execute(
            text("CALL sp_linestat_shift_sequence('spamso', :lineno, NULL)"),
            {'lineno': lineno}
        )
        db.session.execute(
            text("CALL sp_linestat_shift_sequence('wci', :lineno, NULL)"),
            {'lineno': lineno}
        )
        db.session.execute(
            text("CALL sp_linestat_shift_sequence('rit', :lineno, NULL)"),
            {'lineno': lineno}
        )
        db.session.execute(
            text("CALL sp_linestat_shift_sequence('fit', :lineno, NULL)"),
            {'lineno': lineno}
        )
        db.session.execute(
            text("CALL sp_linestat_shift_sequence('pit', :lineno, NULL)"),
            {'lineno': lineno}
        )
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing line: {e}")
        return False

def force_restart_for_manual_edit():
    """Call this when a WorkSched is manually edited to trigger a PLC restart."""
    stat = get_current_linestat()
    stat.updtime = datetime.now()
    db.session.commit()

def trigger_shift_if_zero(lineno, station, modelcode):
    """Call this if a manual edit forces a variance to exactly 0."""
    try:
        db.session.execute(
            text("CALL sp_linestat_shift_sequence(:station, :lineno, :modelcode)"),
            {'station': station, 'lineno': lineno, 'modelcode': modelcode}
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error shifting sequence manually: {e}")
