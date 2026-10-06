def correct_input() -> int:
    """Функция проверяет корректность данных, введенных пользователем."""
    while True:
        try:
            n = int(input("Введите n: "))
            if n < 0:
                print("n должно быть целым неотрицательным числом. "
                      "Попробуйте снова.")
                continue
            return n
        except ValueError:
            print("Некорректный ввод. Введите целое число.")


def main() -> None:
    """Функция выводит n первых элементов последовательности 122333..."""
    n: int = correct_input()
    result: list[str] = []
    item: int = 1
    count: int = 0

    while count < n:
        add_count: int = min(item, n - count)
        result.append(str(item) * add_count)
        item += 1
        count += add_count
    print(''.join(result))


if __name__ == '__main__':
    main()
