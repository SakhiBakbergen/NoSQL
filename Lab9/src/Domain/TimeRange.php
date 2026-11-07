<?php
declare(strict_types=1);

namespace App\Domain;

/** Объект-значение: интервал времени консультации. */
final readonly class TimeRange
{
    public const MIN_MINUTES = 15;

    public function __construct(
        public \DateTimeImmutable $start,
        public \DateTimeImmutable $end,
    ) {
        if ($end <= $start) {
            throw new \InvalidArgumentException('Конец слота должен быть позже начала.');
        }
        if ($this->minutes() < self::MIN_MINUTES) {
            throw new \InvalidArgumentException(
                'Минимальная длительность слота — ' . self::MIN_MINUTES . ' минут.'
            );
        }
    }

    public function minutes(): int
    {
        return intdiv($this->end->getTimestamp() - $this->start->getTimestamp(), 60);
    }

    public function overlaps(self $other): bool
    {
        return $this->start < $other->end && $other->start < $this->end;
    }

    public function label(): string
    {
        return $this->start->format('d.m.Y H:i') . '–' . $this->end->format('H:i');
    }
}
