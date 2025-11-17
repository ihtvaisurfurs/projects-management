from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from core.constants import (
    ADMIN_MENU_BUTTONS,
    USER_MENU_BUTTONS,
    BACK_TO_MENU,
    PROGRAMMER_MENU_BUTTONS,
    REQUEST_PHONE_BUTTON,
    SKIP_DESCRIPTION_BUTTON,
    SKIP_OWNER_BUTTON,
)


def contact_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=REQUEST_PHONE_BUTTON, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [
            KeyboardButton(text=ADMIN_MENU_BUTTONS[0]),
            KeyboardButton(text=ADMIN_MENU_BUTTONS[1]),
        ],
        [KeyboardButton(text=ADMIN_MENU_BUTTONS[2])],
        [KeyboardButton(text=ADMIN_MENU_BUTTONS[3])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def user_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=USER_MENU_BUTTONS[0])],
        [KeyboardButton(text=USER_MENU_BUTTONS[1])],
        [KeyboardButton(text=USER_MENU_BUTTONS[2])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def programmer_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=text)] for text in PROGRAMMER_MENU_BUTTONS]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BACK_TO_MENU)]],
        resize_keyboard=True,
    )


def owner_skip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=SKIP_OWNER_BUTTON)],
            [KeyboardButton(text=BACK_TO_MENU)],
        ],
        resize_keyboard=True,
    )


def description_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=SKIP_DESCRIPTION_BUTTON)],
            [KeyboardButton(text=BACK_TO_MENU)],
        ],
        resize_keyboard=True,
    )
