import multiprocessing
import os
import time


MAX_PROCESSES = multiprocessing.cpu_count()  
CHUNK_SIZE = 4096 
script_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_FILENAME = os.path.join(script_dir, "input.txt") 
OUTPUT_FILENAME = os.path.join(script_dir, "output.txt")  


# функция шифра, в данном случае - цезарь
def caesar_cipher(text, key, decrypt=False):
    result = ''
    for char in text:
        if char.isalpha():
            start = ord('a') if char.islower() else ord('A')
            shifted_char = chr((ord(char) - start + (key if not decrypt else -key)) % 26 + start)
        else:
            shifted_char = char 
        result += shifted_char
    return result

#для фонового процесса, в очередь
def process_chunk(chunk, key, encrypt, queue):
    try:
        if encrypt:
            encrypted_chunk = caesar_cipher(chunk, key)
            queue.put(encrypted_chunk)
        else:
            decrypted_chunk = caesar_cipher(chunk, key, decrypt=True)
            queue.put(decrypted_chunk)
    except Exception as e:
        print(f"Ошибка в процессе: {e}")
        queue.put(None)  

#результаты(в фоновке)
def writer_process(queue, output_filename):
    try:
        with open(output_filename, 'w', encoding='utf-8') as outfile:
            while True:
                result = queue.get()
                if result is None: 
                    print("Ошибка, запись прекращена.")
                    return
                if result == "DONE":
                    break
                outfile.write(result)
    except Exception as e:
        print(f"Ошибка записи в файл: {e}")

#функция шифра и дешифра
def encrypt_decrypt_file(input_filename, output_filename, key, encrypt, num_processes):
    try:
        file_size = os.path.getsize(input_filename)


        cpu_load = 25  
        available_processes = int(num_processes * (1 - cpu_load / 100))
        num_processes = min(available_processes, MAX_PROCESSES)
        print(f"Используется {num_processes} процессов.")

        queue = multiprocessing.Queue()
        processes = []

        # запуск фоновог процесса
        writer = multiprocessing.Process(target=writer_process, args=(queue, output_filename))
        writer.start()

        with open(input_filename, 'r', encoding='utf-8') as infile:
            chunk = infile.read(CHUNK_SIZE)
            while chunk:

                p = multiprocessing.Process(target=process_chunk, args=(chunk, key, encrypt, queue))
                processes.append(p)
                p.start()

                chunk = infile.read(CHUNK_SIZE) 
        
        for p in processes:
            p.join()
        
        queue.put("DONE")  
        writer.join()

    except FileNotFoundError:
        print("Файл не найден.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

# --- Функция для выбора количества процессов  ---
def get_num_processes():
    while True:
        try:
            num_processes = int(input(f"Введите количество процессов (максимум {MAX_PROCESSES}): "))
            if 1 <= num_processes <= MAX_PROCESSES:
                return num_processes
            else:
                print("Некорректное количество процессов. Пожалуйста, введите число от 1 до", MAX_PROCESSES)
        except ValueError:
            print("Некорректный ввод. Пожалуйста, введите целое число.")

# --- Главная функция ---
def main():
    print("Шифратор/Дешифратор файла")
    #input_filename = input("Введите путь к входному файлу: ")
    #output_filename = input("Введите путь к выходному файлу: ")
    key = int(input("Введите ключ шифрования (целое число): "))
    num_processes = get_num_processes()  

    action = input("Шифровать (e) или дешифровать (d)? ").lower()

    if action == 'e':
        encrypt_decrypt_file(INPUT_FILENAME, OUTPUT_FILENAME, key, True, num_processes)
        print("Файл зашифрован.")
    elif action == 'd':
        encrypt_decrypt_file(INPUT_FILENAME, OUTPUT_FILENAME, key, False, num_processes)
        print("Файл дешифрован.")
    else:
        print("Некорректное действие.")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
