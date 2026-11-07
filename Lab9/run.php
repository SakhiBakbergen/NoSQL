<?php
declare(strict_types=1);

require dirname(__DIR__) . '/src/bootstrap.php';

use App\Domain\{Schedule, Student, Teacher, TimeRange, User};

$passed = 0;
$failed = 0;

function ok(bool $cond, string $name): void
{
    global $passed, $failed;
    if ($cond) { $passed++; echo "OK:   $name\n"; }
    else       { $failed++; echo "FAIL: $name\n"; }
}

function expectException(string $class, callable $action, string $name): void
{
    global $passed, $failed;
    try {
        $action();
        $failed++;
        echo "FAIL: $name (исключения нет)\n";
    } catch (Throwable $e) {
        if ($e instanceof $class) {
            $passed++;
            echo "OK:   $name — {$e->getMessage()}\n";
        } else {
            $failed++;
            echo "FAIL: $name (получен " . $e::class . ")\n";
        }
    }
}

function range_(string $from, string $to): TimeRange
{
    return new TimeRange(new DateTimeImmutable("2026-11-10 $from"), new DateTimeImmutable("2026-11-10 $to"));
}

$teacher = new Teacher(1, 'Анна Ким', 'a.kim@atu.edu.kz', 'ИТ');
$s1 = new Student(10, 'Алия Нур', 'a@example.kz', 'ИС');
$s2 = new Student(11, 'Данияр Серик', 'd@example.kz', 'ИС');

// 1. Корректные объекты
ok($s1->id === 10 && $teacher->id === 1, '1. Корректные Student и Teacher созданы');

// 2. Пустое имя
expectException(InvalidArgumentException::class, fn() => new Student(12, '', 'x@example.kz', 'ИС'), '2. Пустое имя');

// 3. Неверный email
expectException(InvalidArgumentException::class, fn() => new Student(12, 'Иван Иванов', 'bad-email', 'ИС'), '3. Неверный email');

// 4. Конец раньше начала
expectException(InvalidArgumentException::class, fn() => range_('11:00', '10:00'), '4. Конец слота раньше начала');

// 5. Граница длительности: 14 минут — ошибка, 15 — успех
expectException(InvalidArgumentException::class, fn() => range_('10:00', '10:14'), '5a. Слот 14 минут (граница)');
ok(range_('10:00', '10:15')->minutes() === 15, '5b. Слот ровно 15 минут допустим');

// 6. Успешная запись
$schedule = new Schedule($teacher);
$slot1 = $schedule->addSlot(range_('10:00', '10:30'));
$slot2 = $schedule->addSlot(range_('11:00', '11:30'));
$a = $schedule->book($s1, $slot1->id);
ok($a->studentId === 10 && $slot1->isBusy(), '6. Студент записан, слот занят');

// 7. Занятый слот
expectException(DomainException::class, fn() => $schedule->book($s2, $slot1->id), '7. Запись на занятый слот');

// 8. Дубль: тот же студент на другой (свободный) слот
expectException(DomainException::class, fn() => $schedule->book($s1, $slot2->id), '8. Повторная запись студента');
ok(!$slot2->isBusy(), '8b. После ошибки второй слот остался свободным');

// 9. Пересечение слотов
expectException(DomainException::class, fn() => $schedule->addSlot(range_('10:15', '10:45')), '9. Пересечение слотов');

// 10. Полиморфизм
$labels = array_map(fn(User $u) => $u->roleLabel(), [$teacher, $s1]);
ok($labels[0] !== $labels[1], '10. Разные подписи ролей: ' . implode(' | ', $labels));

// 11. readonly ID
try {
    $s1->id = 99;
    ok(false, '11. Изменение readonly ID');
} catch (Error $e) {
    ok(true, '11. Изменение readonly ID запрещено — ' . $e->getMessage());
}

echo "\nИтого: OK = $passed, FAIL = $failed\n";
exit($failed === 0 ? 0 : 1);
