# Lab 13, вариант 2 (Библиотека): проверка RBAC на Java

Программа подключается под `lib_viewer`, `lib_editor`, `lib_auditor` и выполняет 15 проверок
(6 разрешённых, 9 запрещённых). Результат выводится в консоль и сохраняется в `results.md`
(готовая таблица для отчёта).

## Запуск в IntelliJ IDEA Community 2024.2

1. **File → Open** и выберите папку `library-rbac-lab` (или `pom.xml`) → *Open as Project*.
2. **File → Project Structure → Project → SDK**: JDK 17 или новее (подойдёт встроенный JBR 21).
3. Дождитесь загрузки Maven-зависимостей (или нажмите кнопку Reload в панели Maven).
4. В mongosh (под `labadmin`) должны быть выполнены seed-данные, создание ролей и пользователей из отчёта.
5. Откройте `src/main/java/lab13/RbacLabTests.java` → зелёная стрелка у `main` → **Modify Run Configuration**.
6. В поле **Environment variables** (Modify options → Environment variables) задайте:

   ```
   LAB13_PWD_LIB_VIEWER=...;LAB13_PWD_LIB_EDITOR=...;LAB13_PWD_LIB_AUDITOR=...
   ```

   Если переменные не заданы, программа спросит пароль в консоли (в окне Run ввод будет виден).
7. Запустите **Run**. Для скриншотов закройте окно Environment variables, чтобы пароли не попали в кадр.

## Важно

- Пароли в коде и в репозитории не хранятся. Не добавляйте файл `.idea/` с Run Configuration в Git
  (это уже учтено в `.gitignore`).
- Тест T11 пытается выполнить `drop` для `books` под `lib_editor`. При правильных ролях он отклоняется
  с `Unauthorized`. Если он вдруг прошёл, это ошибка в роли, а данные нужно заново залить seed-скриптом.
- Если все тесты падают с `OTHER_ERROR` и сообщением об аутентификации, проверьте пароль и то, что
  `authenticationDatabase` совпадает с базой `library_lab13`, где создавались пользователи.
