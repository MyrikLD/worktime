#!/bin/python3
import os

import notify2

notify2.init('WORKTIMER')


class Notify:
    _files = ['emoticon', 'kmousetool_off']

    def __init__(self, num):
        self._num = num

    def send(self, header, text):
        if not self:
            n = notify2.Notification(
                header,
                text,
                self._files[self._num]
            )
            n.show()
            open('.' + self._files[self._num], 'w').close()

    @staticmethod
    def show(header, text, file=''):
        print(text)
        n = notify2.Notification(header, text, file)
        n.show()

    def __bool__(self):
        return '.' + self._files[self._num] in os.listdir('/home/myrik/.work')

    @classmethod
    def clean(cls):
        for i in cls._files:
            try:
                os.remove('.' + i)
            except:
                pass


if __name__ == "__main__":
    Notify.show('TEST', 'TEST', 'emoticon')
    Notify.show('TEST', 'TEST', 'kmousetool_off')
