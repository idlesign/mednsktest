#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re


from random import shuffle, choice


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
    variants = map(lambda x: str(x), range(1, len(question_data_answers)+1))
    right_answer_idx = None

    for idx, ans in enumerate(question_data_answers):
        answers.append('  %s. %s' % (idx+1, ans[0]))
        if ans[1]:
            right_answer_idx = idx

    def get_input():
        question_text = '%s:\n%s\n> ' % (question_data['question'], '\n'.join(answers))
        user_input = raw_input(question_text)
        if user_input not in variants:
            print('Нужно выбрать один из следующих вариантов: %s.\n' % ', '.join(variants))
            return get_input()
        return user_input

    inp = get_input()
    text_cool = ['Обалдеть', 'Отлично', 'Замечательно', 'Чудесно', 'Классно', 'Ура', 'Ваще чума', 'Ёлки', 'Вот так дела', 'Ой-вей', 'Недурно']

    success = ((int(inp)-1) == right_answer_idx)

    if success:
        print('%s, это правильный ответ!' % choice(text_cool))
    else:
        print('Неверно! Правильный ответ: %s. %s' % (right_answer_idx+1, question_data_answers[right_answer_idx][0]))

    return success


def process_questions(questions, shuffle_answers=False):
    """Запускает процедуру опроса пользователя по указанным вопросам."""
    failures = []
    total = len(questions)
    for idx, question_data in enumerate(questions, 1):
        print('\n\nВопрос %s из %s (%s)' % (idx, total, question_data['question_num']))
        if not process_question(question_data, shuffle_answers=shuffle_answers):
            failures.append(question_data)
    return failures
