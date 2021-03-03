# content of test_activity_maps.py
from premise.activity_maps import InventorySet

dummy_minimal_db = [{'name': 'electricity production, at BIGCC power plant 450MW, pre, pipeline 200km, storage 1000m'},
                    {'name': 'electricity production, at BIGCC power plant 450MW, no CCS'},
                    {'name': 'electricity production, at power plant/lignite, IGCC, no CCS'},
                    {'name': 'electricity production, at power plant/hard coal, pre, pipeline 200km, storage 1000m'},
                    {'name': 'electricity production, at power plant/hard coal, post, pipeline 200km, storage 1000m'},
                    {'name': 'electricity production, at power plant/natural gas, pre, pipeline 200km, storage 1000m'},
                    {'name': 'heat and power co-generation, biogas, gas engine, label-certified'},
                    {'name': 'electricity production, hard coal'},
                    {'name': 'heat and power co-generation, hard coal'},
                    {'name': 'electricity production, natural gas, conventional power plant'},
                    {'name': 'electricity production, natural gas, combined cycle power plant'},
                    {'name': 'heat and power co-generation, natural gas, conventional power plant, 100MW electrical'},
                    {'name': 'electricity production, deep geothermal'},
                    {'name': 'electricity production, hydro, reservoir, tropical region'},
                    {'name': 'electricity production, nuclear, pressure water reactor'},
                    {'name': 'electricity production, oil'},
                    {'name': 'electricity production, solar thermal parabolic trough, 50 MW'},
                    {
                        'name': 'electricity production, photovoltaic, 3kWp facade installation, multi-Si, laminated, integrated'},
                    {'name': 'electricity production, wind, 2.3MW turbine, precast concrete tower, onshore'},
                    {'name': 'steel production'},
                    {'name': 'market for aluminium, primary'}]

for act in dummy_minimal_db:
    act["location"] = "DE"
    act["unit"] = "kilowatt hour"
    act["reference product"] = "electricity"


def test_presence_of_dict():
    maps = InventorySet(dummy_minimal_db)
    assert isinstance(maps.get_remind_to_ecoinvent_emissions(), dict)
    assert isinstance(maps.generate_material_map(), dict)
    assert isinstance(maps.generate_powerplant_map(), dict)


def test_length_dict():
    maps = InventorySet(dummy_minimal_db)
    assert len(maps.get_remind_to_ecoinvent_emissions()) > 0
    assert len(maps.generate_material_map()) > 0
    assert len(maps.generate_powerplant_map()) > 0


def test_content_dict():
    maps = InventorySet(dummy_minimal_db)
    materials = maps.generate_material_map()
    assert materials['aluminium'] == {'market for aluminium, primary'}
    plants = maps.generate_powerplant_map()
    assert plants['Coal IGCC'] == {'electricity production, at power plant/lignite, IGCC, no CCS'}
    emissions = maps.get_remind_to_ecoinvent_emissions()
    assert emissions['Sulfur dioxide'] == 'SO2'
