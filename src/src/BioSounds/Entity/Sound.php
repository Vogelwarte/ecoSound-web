<?php

namespace BioSounds\Entity;


class Sound
{
    const TABLE_NAME = 'sound';
    const SOUND_ID = 'sound_id';
    const PHONY = 'phony';
    const SOUND_TYPE = 'sound_type';

    /**
     * @var int
     */
    private $sound_id;

    /**
     * @var string
     */
    private $phony;

    /**
     * @var string
     */
    private $sound_type;

    /**
     * @return int
     */
    public function getSoundId(): int
    {
        return $this->sound_id;
    }

    /**
     * @param int $sound_id
     * @return Sound
     */
    public function setSoundId(int $sound_id): Sound
    {
        $this->sound_id = $sound_id;
        return $this;
    }

    /**
     * @return null|string
     */
    public function getPhony(): ?string
    {
        return $this->phony;
    }

    /**
     * @param null|string $phony
     * @return Sound
     */
    public function setPhony(?string $phony): Sound
    {
        $this->phony = $phony;
        return $this;
    }

    /**
     * @return null|string
     */
    public function getSoundType(): ?string
    {
        return $this->sound_type;
    }

    /**
     * @param null|string $sound_type
     * @return Sound
     */
    public function setSoundType(?string $sound_type): Sound
    {
        $this->sound_type = $sound_type;
        return $this;
    }
}
