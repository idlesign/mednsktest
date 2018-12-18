# -*- coding: utf-8 -*-
import json
import os
import re
import sys
from random import shuffle, choice

import click

from mednsktest import VERSION_STR

PY3 = sys.version_info[0] == 3

PATH_REPO = os.path.join(os.path.dirname(__file__), 'repo')

RE_QUESTION = re.compile(
    '(?P<question_num>[^\n]+)\n(?P<question>[^#]+)\n'
    '#Варианты к вопросу[^\n]+\n(?P<answers>[^#]+)\n'
    '#Ответ(?P<answer_num>[^\n]+)\n', re.U)

RE_QUESTION_BOUNDARY = re.compile('#Вопрос', re.U)
RE_ANSWER = re.compile('[^\d]{0,1}(\d+)\.(.+)', re.U | re.M)

RIGHT_ANSWER_MARKER = '*****'


def get_question_from_file(fname):
    """Считывает данные из файла-вопросника. Возвращает словарь с этими данными."""

    with open(fname) as f:
        data = f.read()

    questions = []

    for question_entry in re.split(RE_QUESTION_BOUNDARY, data):
        question_data = re.search(RE_QUESTION, question_entry)

        if question_data is not None:
            question_data = question_data.groupdict()
            for k, v in question_data.items():
                question_data[k] = v.strip(' :.')

            answers_src = re.findall(RE_ANSWER, question_data['answers'])
            answers = []
            right_answer = int(question_data['answer_num'])
            if right_answer > len(answers_src):
                right_answer = 0

            right_exists = False

            for answer_id, answer in answers_src:
                is_right = (int(answer_id) == right_answer)

                if not right_answer and RIGHT_ANSWER_MARKER in answer:
                    is_right = True
                answer = answer.replace(RIGHT_ANSWER_MARKER, '').strip(' ;.')
                answers.append((answer, is_right))
                if is_right:
                    right_exists = True

            if not right_exists:
                raise Exception('Не определен правильный ответ для вопроса %s' % question_data['question_num'])

            question_data['answers'] = answers
            questions.append(question_data)

    return questions


def process_question(question_data, shuffle_answers=False):
    """Выводит вопрос пользователю и обрабатывает ответ на него.
    Возвращает булево, указывающее на правильность ответа пользователя.

    """
    question_data_answers = question_data['answers'][:]

    if shuffle_answers:
        shuffle(question_data_answers)

    answers = []
    variants = list(map(lambda x: str(x), range(1, len(question_data_answers) + 1)))
    right_answer_idx = None

    for idx, ans in enumerate(question_data_answers):
        answers.append('  %s. %s' % (idx + 1, ans[0]))
        if ans[1]:
            right_answer_idx = idx

    def get_input(question_text):
        user_input = click.prompt(question_text)

        if user_input not in variants:
            click.secho('Нужно выбрать один из следующих вариантов: %s.\n' % ', '.join(variants), fg='red')
            return get_input('')

        return user_input

    inp = get_input('%s:\n%s\n> ' % (question_data['question'], '\n'.join(answers)))

    text_cool = [
        'Обалдеть',
        'Отлично',
        'Замечательно',
        'Чудесно',
        'Классно',
        'Ура',
        'Ваще чума',
        'Ёлки',
        'Вот так дела',
        'Ой-вей',
        'Недурно'
    ]

    success = ((int(inp) - 1) == right_answer_idx)

    if success:
        msg = '%s, это правильный ответ!' % choice(text_cool)

    else:
        msg = 'Неверно! Правильный ответ: %s. %s' % (right_answer_idx + 1, question_data_answers[right_answer_idx][0])

    return success, msg


def process_questions(questions, shuffle_answers=False):
    """Запускает процедуру опроса пользователя по указанным вопросам."""
    failures = []
    successes = []

    total = len(questions)

    for idx, question_data in enumerate(questions, 1):
        click.secho('\n\nВопрос %s из %s (%s)' % (idx, total, question_data['question_num']))

        success, msg = process_question(question_data, shuffle_answers=shuffle_answers)

        click.secho(msg, fg='green' if success else 'red')

        (successes if success else failures).append(question_data)

    return successes, failures


def get_repo_filenames():
    filenames = sorted((
        f.strip('.txt') for f in os.listdir(PATH_REPO)
        if os.path.splitext(os.path.join(PATH_REPO, f))[-1] == '.txt'), reverse=True)
    return filenames


REPO_FILENAMES = get_repo_filenames()


class Store(object):

    def __init__(self, repo_name):
        self.path = os.path.join(os.path.abspath(os.getcwd()), 'mednsktest_%s.tmp' % repo_name)
        self.success = []
        self.fail = []

    def filter_questions(self, questions):
        seen = set(self.success + self.fail)

        questions_ = []

        for question in questions:
            if question['question_num'] in seen:
                continue
            questions_.append(question)

        return questions_

    def load(self):
        path = self.path

        if not os.path.isfile(path):
            return

        with open(path) as f:
            data = json.loads(f.read())

        self.success = data['success']
        self.fail = data['fail']

    def contribute(self, successes, failures):

        def extend(container, questions):
            container.extend([question['question_num'] for question in questions])

        extend(self.success, successes)
        extend(self.fail, failures)

    def save(self):
        with open(self.path, 'w') as f:
            f.write(json.dumps({
                'success': list(set(self.success)),
                'fail': list(set(self.fail)),
            }))


def help(val):
    if PY3:
        return val
    return val.decode('utf-8')


@click.group()
@click.version_option(version=VERSION_STR)
def base():
    """Тесты с курсов НГМУ. Консольное приложение."""


@base.command()
@click.argument('filename', type=click.Choice(REPO_FILENAMES), default=REPO_FILENAMES[0])
@click.option(
    '--qlimit', help=help('Ограничение количества вопросов на сеанс'), type=int, default=50)
@click.option(
    '--ashuffle', help=help('Если флаг задан, ответы будут перетасованы'), is_flag=True)
@click.option(
    '--save', help=help('Сохранить прогресс тестирования (не задавать вопросы из предыдущих сеансов)'), is_flag=True)
def start(filename, qlimit, ashuffle, save):
    """Стартует опрос."""

    def print_summary(total, failures):
        num_fail = len(failures)
        num_success = (total - num_fail)
        rate = round(num_success * 100 / total)

        click.secho('\n==============================\nИтого:\n  всего вопросов - %s' % total)
        click.secho('  верных ответов - %s' % num_success, fg='green')
        click.secho('  ошибок - %s' % num_fail, fg='red')
        click.secho('  успешность - %s%%' % rate, fg='cyan')

    def process_failures(failures):
        # Повторим вопросы с ошибками.
        if not failures:
            return
        click.secho('\n\nПочти закончили, но теперь повторим вопросы с ошибками:', fg='magenta')
        process_questions(failures)

    store = Store(filename)
    store.load()

    questions = get_question_from_file(os.path.join(PATH_REPO, '%s.txt' % filename))

    shuffle(questions)

    questions = store.filter_questions(questions)

    if save:
        click.secho('Используются данные предыдущих сеансов из %s' % store.path, fg='blue')

    click.secho('Возможных вопросов: %s' % len(questions), fg='cyan')

    questions = questions[:qlimit]

    successes, failures = process_questions(questions, shuffle_answers=ashuffle)

    process_failures(failures)

    print_summary(qlimit, failures)

    if save:
        store.contribute(successes, failures)
        store.save()


def main():
    """
    CLI entry point
    """
    base(obj={})


if __name__ == '__main__':
    main()
