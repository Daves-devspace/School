



def generate_room_name_from_grade_section(grade, section):
    grade_name = grade.name.strip()
    section_name = section.name.strip()
    return f"{grade_name[0].upper()}{grade.level}{section_name[0].upper()}"
