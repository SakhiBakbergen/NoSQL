<?php
declare(strict_types=1);

namespace App\Domain;

final class Student extends User
{
    public function __construct(
        int $id,
        string $fullName,
        string $email,
        public readonly string $program,
    ) {
        parent::__construct($id, $fullName, $email);
        if (trim($program) === '') {
            throw new \InvalidArgumentException('Программа обязательна.');
        }
    }

    #[\Override]
    public function roleLabel(): string
    {
        return 'Студент ' . $this->program;
    }
}
