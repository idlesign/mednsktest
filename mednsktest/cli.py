# -*- coding: utf-8 -*-
import argparse
import sys

from mednsktest import VERSION_STR
from mednsktest.toolbox import *


def main():

    question_files = sorted((
        f.strip('.txt') for f in os.listdir(PATH_REPO)
        if os.path.splitext(os.path.join(PATH_REPO, f))[-1] == '.txt'), reverse=True)

    arg_parser = argparse.ArgumentParser(
        prog='mednsktest',
        description=(
                'Тесты с курсов НГМУ. Консольное приложение\n\n'
                'Имеющиеся вопросники:\n%s' % ' '.join(question_files)))

    arg_parser.add_argument('filename', help='Имя вопросника (файла с вопросами без расширения .txt)')
    arg_parser.add_argument('--questions_limit', help='Ограничение количества вопросов на сеанс', default=50)
    arg_parser.add_argument('--shuffle_answers', help='Если флаг задан, ответы будут перетасованы', action='store_true')
    arg_parser.add_argument('--version', action='version', version='%s %s' % ('%(prog)s', VERSION_STR))

    parsed_args = arg_parser.parse_args()

    questions_limit = int(parsed_args.questions_limit)

    questions = get_question_from_file(os.path.join(PATH_REPO, '%s.txt' % parsed_args.filename))
    shuffle(questions)
    questions = questions[:questions_limit]

    failures = process_questions(questions, shuffle_answers=parsed_args.shuffle_answers)

    # Повторим вопросы с ошибками.
    if failures:
        print('\n\nПочти закончили, но теперь повторим вопросы с ошибками:\n')
        process_questions(failures)

    num_fail = len(failures)
    num_success = (questions_limit-num_fail)
    rate = (num_success*100 / questions_limit)

    print(
        '\n==============================\n'
        'Итого:\n  всего вопросов - %s\n'
        '  верных ответов - %s\n'
        '  ошибок - %s\n'
        '  успешность - %s%%' % (questions_limit, num_success, num_fail, round(rate, 0)))

    sys.exit(1)
