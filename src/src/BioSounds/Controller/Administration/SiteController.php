<?php

namespace BioSounds\Controller\Administration;

use BioSounds\Controller\BaseController;
use BioSounds\Entity\Explore;
use BioSounds\Entity\Sensor;
use BioSounds\Entity\Site;
use BioSounds\Exception\ForbiddenException;
use BioSounds\Provider\BaseProvider;
use BioSounds\Provider\ProjectProvider;
use BioSounds\Provider\SiteProvider;
use BioSounds\Utils\Auth;


class SiteController extends BaseController
{
    const SECTION_TITLE = 'Site';

    /**
     * @return false|string
     * @throws \Exception
     */
    public function show($projectId = null)
    {
        if (!Auth::isManage()) {
            throw new ForbiddenException();
        }
        if (isset($_GET['projectId'])) {
            $projectId = $_GET['projectId'];
        }
        $projects = (new ProjectProvider())->getWithPermission(Auth::getUserID());
        if (empty($projectId)) {
            $projectId = $projects[0]->getId();
        }
        $arr = [];
        $siteProvider = new SiteProvider();
        $explores = (new Explore())->getAllExplores();
        foreach ($explores as $explore) {
            $arr['pid' . $explore['pid']]['id' . $explore['explore_id']] = [$explore['explore_id'], $explore['name']];
        }
        return $this->twig->render('administration/sites.html.twig', [
            'projects' => $projects,
            'projectId' => $projectId,
            'explores' => $arr,
            'realms' => (new Explore())->getExplores(),
            'siteList' => $siteProvider->getList($projectId),
            'gadm0' => json_decode($this->gadm()),
        ]);
    }

    /**
     * @return bool
     * @throws \Exception
     */
    public function save()
    {
        $siteEnt = new Site();

        if (!Auth::isManage()) {
            throw new ForbiddenException();
        }

        $data = [];
        $sitePdoValue = '';
        foreach ($_POST as $key => $value) {
            if (strrpos($key, '_')) {
                $type = substr($key, strrpos($key, '_') + 1, strlen($key));
                $key = substr($key, 0, strrpos($key, '_'));
            }
            $sitePdoValue = $value;
            if ($sitePdoValue != '0' && empty($sitePdoValue)) {
                $sitePdoValue = '';
            }
            switch ($key) {
                case 'realm_id':
                    $data['realm_id'] = $sitePdoValue == '' ? 0 : $sitePdoValue;
                    break;
                case 'biome_id':
                    $data['biome_id'] = $sitePdoValue == '' ? 0 : $sitePdoValue;
                    break;
                case 'functional_group_id':
                    $data['functional_group_id'] = $sitePdoValue == '' ? 0 : $sitePdoValue;
                    break;
                case 'longitude':
                    $data['longitude_WGS84_dd_dddd'] = $sitePdoValue == '' ? null : $sitePdoValue;
                    break;
                case 'latitude':
                    $data['latitude_WGS84_dd_dddd'] = $sitePdoValue == '' ? null : $sitePdoValue;
                    break;
                default:
                    $data[$key] = $sitePdoValue;
            }
        }

        if (isset($data['steId'])) {
            $siteEnt->update($data);
            return json_encode([
                'errorCode' => 0,
                'message' => 'Site updated successfully.',
            ]);
        } else {
            $data['creation_date_time'] = date('Y-m-d H:i:s', time());
            $data['user_id'] = Auth::getUserID();

            if ($siteEnt->insert($data) > 0) {
                return json_encode([
                    'errorCode' => 0,
                    'message' => 'Site created successfully.',
                ]);
            }
        }
    }

    /**
     * @param int $id
     * @return false|string
     * @throws \Exception
     */
    public function delete(int $id)
    {
        if (!Auth::isManage()) {
            throw new ForbiddenException();
        }

        if (empty($id)) {
            throw new \Exception(ERROR_EMPTY_ID);
        }

        $siteProvider = new SiteProvider();
        $siteProvider->delete($id);

        return json_encode([
            'errorCode' => 0,
            'message' => 'Site deleted successfully.',
        ]);
    }

    public function getExplore(int $pid = 0)
    {
        $explores = (new Explore())->getExplores($pid);
        return json_encode($explores);
    }

    public function gadm(int $level = 0, string $pid = '0')
    {
        return json_encode((new SiteProvider())->getGamds($level, $pid));
    }
}
