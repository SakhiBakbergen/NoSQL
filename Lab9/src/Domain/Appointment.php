<?php
declare(strict_types=1);

namespace App\Domain;

/** Факт записи студента на слот. */
final readonly class Appointment
{
    public function __construct(
        public int $studentId,
        public int $slotId,
        public \DateTimeImmutable $createdAt,
    ) {
        if ($studentId < 1) {
            throw new \InvalidArgumentException('Некорректный ID студента.');
        }
        if ($slotId < 1) {
            throw new \InvalidArgumentException('Некорректный ID слота.');
        }
    }
}
