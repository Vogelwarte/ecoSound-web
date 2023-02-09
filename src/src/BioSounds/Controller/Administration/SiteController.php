<?php

namespace BioSounds\Controller\Administration;

use BioSounds\Controller\BaseController;
use BioSounds\Entity\IucnGet;
use BioSounds\Entity\Site;
use BioSounds\Entity\SiteCollection;
use BioSounds\Exception\ForbiddenException;
use BioSounds\Provider\CollectionProvider;
use BioSounds\Provider\ProjectProvider;
use BioSounds\Provider\SiteProvider;
use BioSounds\Utils\Auth;


class SiteController extends BaseController
{
    const SECTION_TITLE = 'Site';

    /**
     * @param int|null $projectId
     * @param int|null $collectionId
     * @return false|string
     * @throws \Exception
     */
    public function show($projectId = null, $collectionId = null)
    {
        if (!Auth::isManage()) {
            throw new ForbiddenException();
        }
        if (isset($_GET['projectId'])) {
            $projectId = $_GET['projectId'];
        }
        if (isset($_GET['collectionId'])) {
            $collectionId = $_GET['collectionId'];
        }
        if ($collectionId == '') {
            $collectionId = null;
        }
        $projects = (new ProjectProvider())->getWithPermission(Auth::getUserID());
        if (empty($projectId)) {
            $projectId = $projects[0]->getId();
        }
        $collections = (new CollectionProvider())->getByProject($projectId, Auth::getUserID());
        $arr = [];
        $iucn_gets = (new IucnGet())->getAllIucnGets();
        foreach ($iucn_gets as $iucn_get) {
            $arr['pid' . $iucn_get['pid']]['id' . $iucn_get['iucn_get_id']] = [$iucn_get['iucn_get_id'], $iucn_get['name']];
        }
        return $this->twig->render('administration/sites.html.twig', [
            'projects' => $projects,
            'collections' => $collections,
            'projectId' => $projectId,
            'collectionId' => $collectionId,
            'iucn_gets' => $arr,
            'realms' => (new IucnGet())->getIucnGets(),
            'gadm0' => json_decode($this->gadm()),
        ]);
    }

    public function getListByPage($projectId = null, $collectionId = null)
    {
        $total = (new SiteProvider())->getCount($projectId, $collectionId);
        $start = $_POST['start'];
        $length = $_POST['length'];
        $search = $_POST['search']['value'];
        $column = $_POST['order'][0]['column'];
        $dir = $_POST['order'][0]['dir'];
        $data = (new SiteProvider())->getListByPage($projectId, $collectionId, $start, $length, $search, $column, $dir);
        if(count($data)==0){
            $data=[];
        }
        $result = [
            'draw' => $_POST['draw'],
            'recordsTotal' => $total,
            'recordsFiltered' => (new SiteProvider())->getFilterCount($projectId, $collectionId, $search),
            'data' => $data,
        ];
        return json_encode($result);
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
                case 'project_id':
                    $project_id = $sitePdoValue;
                    break;
                case 'collection_id':
                    $collection_id = $sitePdoValue;
                    break;
                case 'realm_id':
                    $data['realm_id'] = $sitePdoValue == '' ? 0 : $sitePdoValue;
                    break;
                case 'biome_id':
                    $data['biome_id'] = $sitePdoValue == '' ? 0 : $sitePdoValue;
                    break;
                case 'functional_type_id':
                    $data['functional_type_id'] = $sitePdoValue == '' ? 0 : $sitePdoValue;
                    break;
                case 'longitude':
                    $data['longitude_WGS84_dd_dddd'] = $sitePdoValue == '' ? null : $sitePdoValue;
                    break;
                case 'latitude':
                    $data['latitude_WGS84_dd_dddd'] = $sitePdoValue == '' ? null : $sitePdoValue;
                    break;
                case 'topography_m':
                    $data['topography_m'] = $sitePdoValue == '' ? null : $sitePdoValue;
                    break;
                case 'freshwater_depth_m':
                    $data['freshwater_depth_m'] = $sitePdoValue == '' ? null : $sitePdoValue;
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
            $site_id = $siteEnt->insert($data);
            $siteCollection = new SiteCollection();
            if ($collection_id != "") {
                $siteCollection->insert($collection_id, $site_id);
            } else {
                $siteCollection->insertByProject($project_id, $site_id);
            }
            return json_encode([
                'errorCode' => 0,
                'message' => 'Site created successfully.',
            ]);
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

    public function getIucnGet(int $pid = 0)
    {
        $iucn_gets = (new IucnGet())->getIucnGets($pid);
        return json_encode($iucn_gets);
    }

    public function gadm(int $level = 0, string $pid = '0')
    {
        return json_encode((new SiteProvider())->getGamds($level, $pid));
    }
}
