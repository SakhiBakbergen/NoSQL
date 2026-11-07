<?php
declare(strict_types=1);

namespace App\Domain;

final class Teacher extends User
{
    public function __construct(
        int $id,
        string $fullName,
        string $email,
        public readonly string $department,
    ) {
        parent::__construct($id, $fullName, $email);
        if (trim($department) === '') {
            throw new \InvalidArgumentException('Кафедра обязательна.');
        }
    }

    #[\Override]
    public function roleLabel(): string
    {
        return 'Преподаватель ' . $this->department;
    }
}
