<?php
declare(strict_types=1);

namespace App\Domain;

final class TimeSlot
{
    private ?Appointment $appointment = null;

    public function __construct(
        public readonly int $id,
        public readonly Teacher $teacher,   // композиция: слот «имеет» преподавателя
        public readonly TimeRange $range,
    ) {
        if ($id < 1) {
            throw new \InvalidArgumentException('ID слота должен быть положительным.');
        }
    }

    public function book(Student $student): Appointment
    {
        if ($this->isBusy()) {
            throw new \DomainException('Слот уже занят.');
        }
        $this->appointment = new Appointment($student->id, $this->id, new \DateTimeImmutable());
        return $this->appointment;
    }

    public function isBusy(): bool
    {
        return $this->appointment !== null;
    }

    public function appointment(): ?Appointment
    {
        return $this->appointment;
    }
}
