"""Artifact regression fixtures only; no physical print acceptance."""
import copy,io,json,struct,tempfile,unittest,zipfile
from pathlib import Path
import prints

class PrintArtifactTests(unittest.TestCase):
    def fixture(self,offset=0,scale=1,missing=False):
        vertices=[(0,0,0),(1,0,0),(0,1,0),(0,0,1)];triangles=[(0,2,1),(0,1,3),(1,2,3),(2,0,3)]
        stl=b'fixture'.ljust(80,b' ')+struct.pack('<I',4)
        for tri in triangles:stl+=struct.pack('<12fH',0,0,0,*(v for i in tri for v in vertices[i]),0)
        xml='<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" unit="millimeter"><resources><object id="1" type="model"><mesh><vertices>'
        for i,(x,y,z) in enumerate(vertices):xml+=f'<vertex x="{x+(offset if i==1 else 0)}" y="{y}" z="{z}"/>'
        xml+='</vertices><triangles>'
        for a,b,c in triangles[:-1] if missing else triangles:xml+=f'<triangle v1="{a}" v2="{b}" v3="{c}"/>'
        xml+=f'</triangles></mesh></object></resources><build><item objectid="1" transform="{scale} 0 0 0 {scale} 0 0 0 {scale} 150 150 0"/></build></model>'
        data=io.BytesIO()
        with zipfile.ZipFile(data,'w') as archive:archive.writestr('3D/3dmodel.model',xml)
        data.seek(0);return stl,zipfile.ZipFile(data)

    def test_serialization_roundoff_and_translation_allowed(self):
        stl,archive=self.fixture(offset=.000001)
        with archive:self.assertEqual(prints.verify_project_geometry(archive,stl),4)

    def test_geometry_missing_triangle_and_instance_scale_rejected(self):
        for kwargs in [{'offset':.001},{'missing':True},{'scale':2}]:
            stl,archive=self.fixture(**kwargs)
            with self.subTest(kwargs=kwargs),archive,self.assertRaises(ValueError):prints.verify_project_geometry(archive,stl)

    def test_glow_and_silver_use_their_own_material_density(self):
        spec=json.loads((prints.ROOT/'hardware/enclosure/print-spec.json').read_text())
        for part in prints.RINGS:
            self.assertEqual(prints.settings(spec,part,'glow')['filament_density'],'1.5')
            self.assertEqual(prints.settings(spec,part,'silver')['filament_density'],'1.29')
        self.assertEqual(prints.settings(spec,'RearCover','glow')['filament_density'],'1.27')
        self.assertEqual(prints.settings(spec,'InnerDiffuser','glow')['bottom_solid_layers'],'5')
        self.assertEqual(prints.settings(spec,'SideDiffuser','glow')['bottom_solid_layers'],'5')

    def test_print_jobs_retain_native_hashes_bounds_and_sample_parents(self):
        spec=json.loads((prints.ROOT/'hardware/enclosure/print-spec.json').read_text())
        full={'file':'ElectronicsShell.stl','source_part':'ElectronicsShell',
              'sha256':'a'*64,'print_bounds_mm':[200,200,60.6]}
        sample={'file':'FitSideDiffuser.stl','source_part':'SideDiffuser',
                'sha256':'b'*64,'print_bounds_mm':[32,40,20]}
        parts={'stl_files':[full['file']],'print_parts':[full],'fit_samples':[sample]}
        jobs=list(prints.jobs(parts,spec))
        self.assertIs(jobs[0][0],full)
        self.assertEqual(jobs[0][1:],(prints.project_name(full['file'],full['source_part'],'glow'),'glow'))
        rings=[job for job in jobs if job[0] is sample]
        self.assertEqual({material for _,_,material in rings},set(spec['ring_materials']))
        for row,_,_ in jobs:
            self.assertIn('sha256',row)
            self.assertIn('print_bounds_mm',row)

    def test_print_jobs_reject_missing_or_mixed_full_stl_metadata(self):
        spec=json.loads((prints.ROOT/'hardware/enclosure/print-spec.json').read_text())
        for rows in ([],[{'file':'Other.stl','source_part':'Other'}]):
            parts={'stl_files':['ElectronicsShell.stl'],'print_parts':rows,'fit_samples':[]}
            with self.subTest(rows=rows),self.assertRaisesRegex(ValueError,'STL census'):
                list(prints.jobs(parts,spec))

    def test_optical_rings_and_samples_remain_upright_without_supports(self):
        spec=json.loads((prints.ROOT/'hardware/enclosure/print-spec.json').read_text())
        for source in prints.RINGS:
            axis,angle=prints.orientation(source)
            self.assertTrue(angle==0 or axis==[0,0,1])
            for material in spec['ring_materials']:
                self.assertEqual(prints.settings(spec,source,material)['support_material'],'0')
            self.assertEqual(prints.sample_parts()['Fit'+source],source)

    def test_print_layout_rejects_optical_supports_sideways_rings_and_invalid_profiles(self):
        layout=prints.print_layout();bad=[]
        for change in ('optical_support','optical_rotation','unknown_part','duplicate_part','missing_setting','disabled_support'):
            record=copy.deepcopy(layout)
            if change=='optical_support':record['temporary_support_parts'].append('InnerDiffuser')
            elif change=='optical_rotation':record['orientations']['SideDiffuser']={'axis':[1,0,0],'angle_deg':90}
            elif change=='unknown_part':record['temporary_support_parts'].append('UnselectedPart')
            elif change=='duplicate_part':record['temporary_support_parts'].append(record['temporary_support_parts'][0])
            elif change=='missing_setting':del record['temporary_support_settings']['support_material_buildplate_only']
            elif change=='disabled_support':record['temporary_support_settings']['support_material']='0'
            bad.append((change,record))
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'layout.json'
            for change,record in bad:
                path.write_text(json.dumps(record))
                with self.subTest(change=change),self.assertRaises(ValueError):prints.print_layout(path)

    def test_support_toolpaths_must_match_the_selected_profile(self):
        model=';TYPE:External perimeter\n;TYPE:Solid infill\n'
        for role in ('Support material','Support material interface'):
            supported=model+';TYPE:'+role+'\n'
            self.assertTrue(prints.verify_support_toolpaths(supported,{'support_material':'1'},'structural'))
            with self.assertRaisesRegex(ValueError,'support toolpaths'):
                prints.verify_support_toolpaths(supported,{'support_material':'0'},'optical')
        self.assertFalse(prints.verify_support_toolpaths(model,{'support_material':'0'},'optical'))
        with self.assertRaisesRegex(ValueError,'support toolpaths'):
            prints.verify_support_toolpaths(model,{'support_material':'1'},'structural')

    def test_serialized_mesh_bed_normalization_preserves_shape_and_normals(self):
        original,archive=self.fixture();archive.close();data=bytearray(original)
        for i in range(4):
            for j in range(3):
                offset=84+i*50+20+j*12
                struct.pack_into('<f',data,offset,struct.unpack_from('<f',data,offset)[0]+.000418)
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'part.stl';path.write_bytes(data)
            shift=prints.normalize_stl_bed(path);result=path.read_bytes()
            self.assertAlmostEqual(shift,-.000418,places=9)
            heights=[struct.unpack_from('<f',result,84+i*50+20+j*12)[0] for i in range(4) for j in range(3)]
            self.assertEqual(min(heights),0)
            self.assertAlmostEqual(max(heights),1,places=6)
            self.assertEqual(prints.normalize_stl_bed(path),0)
            for i in range(4):
                self.assertEqual(result[84+i*50:96+i*50],original[84+i*50:96+i*50])
                for j in range(3):
                    offset=84+i*50+12+j*12
                    self.assertEqual(result[offset:offset+8],original[offset:offset+8])

if __name__=='__main__':unittest.main()
