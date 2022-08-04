<?php

namespace BioSounds\Entity;

use BioSounds\Provider\BaseProvider;

class Collection extends BaseProvider
{

    const TABLE_NAME = "collection";
    const PRIMARY_KEY = "collection_id";
    const NAME = "name";
    const AUTHOR = "author";
    const DOI = "doi";
    const NOTE = "note";

    const GALLERY_VIEW = 'gallery';
    const LIST_VIEW = 'list';

    /**
     * @var int
     */
    private $id;

    /**
     * @var string
     */
    private $name;

    /**
     * @var int
     */
    private $user_id;

    /**
     * @var string
     */
    private $doi;

    /**
     * @var string
     */
    private $note;

    /**
     * @var string
     */
    private $view = self::GALLERY_VIEW;

    /**
     * @var int
     */
    private $project;

    /**
     * @return int
     */
    public function getId(): int
    {
        return $this->id;
    }

    /**
     * @param int $id
     * @return Collection
     */
    public function setId(int $id): Collection
    {
        $this->id = $id;
        return $this;
    }

    /**
     * @return string
     */
    public function getName(): string
    {
        return $this->name;
    }

    /**
     * @param string $name
     * @return Collection
     */
    public function setName(string $name): Collection
    {
        $this->name = $name;
        return $this;
    }

    /**
     * @return string
     */
    public function getAuthor(): string
    {
        $author = (new User())->getUserName($this->user_id);
        return $author;
    }

    /**
     * @param int $user_id
     * @return Collection
     */
    public function setUserId(string $user_id): Collection
    {
        $this->user_id = $user_id;
        return $this;
    }

    /**
     * @return int
     */
    public function getProject(): int
    {
        return $this->project;
    }

    /**
     * @return null|string
     */
    public function getDoi(): ?string
    {
        return $this->doi;
    }

    /**
     * @param null|string $doi
     * @return Collection
     */
    public function setDoi(?string $doi): Collection
    {
        $this->doi = $doi;
        return $this;
    }

    /**
     * @return null|string
     */
    public function getNote(): ?string
    {
        return $this->note;
    }

    /**
     * @param null|string $note
     * @return Collection
     */
    public function setNote(?string $note): Collection
    {
        $this->note = $note;
        return $this;
    }

    /**
     * @return string
     */
    public function getView(): string
    {
        return $this->view;
    }

    /**
     * @param string $view
     * @return Collection
     */
    public function setView(string $view): Collection
    {
        $this->view = $view;
        return $this;
    }
    /**
     * @return string
     */
    public function getCreationDate(): string
    {
        return $this->creationDate;
    }

    /**
     * @param string $creationDate
     * @return Collection
     */
    public function setCreationDate(string $creationDate): Collection
    {
        $this->creationDate = $creationDate;
        return $this;
    }
    /**
     * @return bool
     */
    public function getPublic(): bool
    {
        return $this->public;
    }

    /**
     * @param bool $public
     * @return Collection
     */
    public function setPublic(bool $public): Collection
    {
        $this->public = $public;
        return $this;
    }
    /**
     * @param int $id
     * @return Collection
     */
    public function setProject(bool $id): Collection
    {
        $this->project = $id;
        return $this;
    }


    /**
     * @param array $collData
     * @return bool
     * @throws \Exception
     */
    public function insertColl(array $collData): bool
    {
        if (empty($collData)) {
            return false;
        }

        $fields = "( ";
        $valuesNames = "( ";
        $values = array();

        foreach ($collData as $key => $value) {
            $fields .= $key;
            $valuesNames .= ":" . $key;
            $values[":" . $key] = $value;
            if (end($collData) !== $value) {
                $fields .= ", ";
                $valuesNames .= ", ";
            }
        }
        $fields .= " )";
        $valuesNames .= " )";

        $this->database->prepareQuery("INSERT INTO collection $fields VALUES $valuesNames");
        return $this->database->executeInsert($values);
    }


    /**
     * @param array $collData
     * @return bool
     * @throws \Exception
     */
    public function updateColl(array $collData): bool
    {
        if (empty($collData)) {
            return false;
        }

        $collId = $collData["collId"];
        unset($collData["collId"]);
        $fields = '';
        $values = [];

        foreach ($collData as $key => $value) {
            $fields .= $key . ' = :' . $key;
            $values[':' . $key] = $value;
            if (end($collData) !== $value) {
                $fields .= ', ';
            }
        }

        $values[':collectionId'] = $collId;
        $this->database->prepareQuery("UPDATE collection SET $fields WHERE collection_id = :collectionId");
        return $this->database->executeUpdate($values);
    }
}