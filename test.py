from requests import get, post, put

URL = 'http://localhost:5000/api/jobs'

def check_change():
    new_job = {
        'job': 'Работа для редактирования',
        'team_leader': 1,
        'work_size': 10,
        'collaborators': '1, 2',
        'is_finished': False
    }
    resp = post(URL, json=new_job)
    
    if resp.ok and 'jobs' in resp.json():
        created_id = resp.json()['jobs']['id']
        print(f"Создана работа с ID: {created_id}")
    else:
        print("Не удалось создать работу, тест прерван.")
        return

    edit_data = {
        'job': 'Обновленное название работы',
        'work_size': 999,
        'is_finished': True
    }
    response = put(f'{URL}/{created_id}', json=edit_data)
    print(f"Статус код (корректный PUT): {response.status_code}")
    try:
        print(f"Ответ: {response.json()}")
    except:
        print(f"Ответ сервера (ошибка):\n{response.text}")

    response_get = get(URL)
    if response_get.ok:
        all_jobs = response_get.json().get('jobs', [])
        updated_job = next((j for j in all_jobs if j['id'] == created_id), None)
        
        if updated_job:
            print(f"Новые данные: {updated_job}")
            if updated_job.get('job') == 'Обновленное название работы' and updated_job.get('work_size') == 999:
                print("Данные успешно изменены!")
            else:
                print("Данные не совпадают с ожидаемыми!")
        else:
            print("Работа не найдена в списке всех работ!")

    response_fail1 = put(f'{URL}/9999', json={'job': 'Не существует'})
    print(f"Статус код (несуществующий ID): {response_fail1.status_code}")
    try: print(f"Ответ: {response_fail1.json()}")
    except: print(f"Ответ: {response_fail1.text}")

    response_fail2 = put(f'{URL}/abc', json={'job': 'Буквы'})
    print(f"Статус код (буквенный ID): {response_fail2.status_code}")
    try: print(f"Ответ: {response_fail2.json()}")
    except: print(f"Ответ: {response_fail2.text}")

    response_fail3 = put(f'{URL}/{created_id}', json={'work_size': 'много'})
    print(f"Статус код (неверный тип данных): {response_fail3.status_code}")
    try: print(f"Ответ: {response_fail3.json()}")
    except: print(f"Ответ: {response_fail3.text}")

    response_fail4 = put(f'{URL}/{created_id}', json={'unknown_field': 'test'})
    print(f"Статус код (недопустимое поле): {response_fail4.status_code}")
    try: print(f"Ответ: {response_fail4.json()}")
    except: print(f"Ответ: {response_fail4.text}")

check_change()