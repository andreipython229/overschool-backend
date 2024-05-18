import re

# формирование массива и кортежей (group, course)
def get_group_course_pairs(params):
    pairs = []
    # Используем регулярное выражение для поиска всех параметров group_name_* и course_name_*
    pattern = re.compile(r'group_name_(\d+_\d+)')

    # Находим все уникальные хвосты индексов
    tails = {match.group(1) for match in pattern.finditer(','.join(params.keys()))}

    for tail in tails:
        group = params.get(f'group_name_{tail}')
        course = params.get(f'course_name_{tail}')

        if group:
            pairs.append((group, course))

    return pairs