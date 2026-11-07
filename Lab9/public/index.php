<?php
declare(strict_types=1);

require dirname(__DIR__) . '/src/bootstrap.php';

use App\Domain\{Schedule, Student, Teacher, TimeRange, User};

function printUserCard(User $user): void
{
    printf(
        "#%d %s — %s <%s>\n",
        $user->id,
        $user->fullName(),
        $user->roleLabel(),
        $user->email,
    );
}

$teacher = new Teacher(1, 'Анна Ким', 'a.kim@atu.edu.kz', 'ИТ');
$student = new Student(10, 'Алия Нур', 'aliya@example.kz', 'ИС');

$schedule = new Schedule($teacher);
$slot = $schedule->addSlot(new TimeRange(
    new DateTimeImmutable('2026-11-10 10:00'),
    new DateTimeImmutable('2026-11-10 10:30'),
));
$schedule->addSlot(new TimeRange(
    new DateTimeImmutable('2026-11-10 11:00'),
    new DateTimeImmutable('2026-11-10 11:30'),
));

$schedule->book($student, $slot->id);

foreach ([$teacher, $student] as $user) {
    printUserCard($user);
}

echo "\nСлоты преподавателя:\n";
foreach ($schedule->slots() as $s) {
    printf("  [%d] %s — %s\n", $s->id, $s->range->label(), $s->isBusy() ? 'занят' : 'свободен');
}
