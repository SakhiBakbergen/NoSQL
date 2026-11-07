<?php
declare(strict_types=1);

namespace App\Domain;

/** Расписание консультаций одного преподавателя. */
final class Schedule
{
    /** @var array<int, TimeSlot> */
    private array $slots = [];
    private int $nextId = 1;

    public function __construct(public readonly Teacher $teacher)
    {
    }

    public function addSlot(TimeRange $range): TimeSlot
    {
        foreach ($this->slots as $slot) {
            if ($slot->range->overlaps($range)) {
                throw new \DomainException('Слот пересекается с существующим.');
            }
        }
        $slot = new TimeSlot($this->nextId++, $this->teacher, $range);
        $this->slots[$slot->id] = $slot;
        return $slot;
    }

    public function book(Student $student, int $slotId): Appointment
    {
        if (!isset($this->slots[$slotId])) {
            throw new \DomainException('Слот не найден.');
        }
        // Сначала все проверки, потом изменение состояния.
        foreach ($this->slots as $slot) {
            if ($slot->appointment()?->studentId === $student->id) {
                throw new \DomainException('Студент уже записан к этому преподавателю.');
            }
        }
        return $this->slots[$slotId]->book($student);
    }

    /** @return list<TimeSlot> */
    public function slots(): array
    {
        return array_values($this->slots);
    }
}
