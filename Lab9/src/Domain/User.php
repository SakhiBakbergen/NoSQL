<?php
declare(strict_types=1);

namespace App\Domain;

abstract class User
{
    public function __construct(
        public readonly int $id,
        private string $fullName,
        public readonly string $email,
    ) {
        if ($id < 1) {
            throw new \InvalidArgumentException('ID должен быть положительным.');
        }
        $this->rename($fullName);
        if (filter_var($email, FILTER_VALIDATE_EMAIL) === false) {
            throw new \InvalidArgumentException('Некорректный email.');
        }
    }

    final public function fullName(): string
    {
        return $this->fullName;
    }

    final public function rename(string $value): void
    {
        $value = trim($value);
        if (preg_match('/^.{3,}$/u', $value) !== 1) {
            throw new \InvalidArgumentException('Имя слишком короткое.');
        }
        $this->fullName = $value;
    }

    abstract public function roleLabel(): string;
}
