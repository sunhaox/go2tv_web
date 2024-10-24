import React, { useState } from 'react';
import { Button, Collapse, message, Popconfirm } from 'antd';
import { DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import type {CollapseProps, PopconfirmProps} from 'antd';
import config from '../config'

const WatchList: React.FC = () => {
    const [messageApi, contextHolder] = message.useMessage();
    const [showInfo, setShowInfo] = useState<CollapseProps['items']>([]);

    const onChange = (key: string | string[]) => {
        console.log(key);
    };

    const onDeleteConfirmClick: PopconfirmProps['onConfirm'] = async (e) => {
        if (!e) {
            return
        }

        const btnId = e.currentTarget.id;
        const name = btnId.substring(4);
        console.log(name);
        message.success('Click on Yes');

        try {
            const response = await fetch(config.host + '/delete_json', {
                method: 'POST',
                headers: new Headers({'Content-Type': 'application/json'}),
                body: JSON.stringify({name: name})
                // TODO change to real name
            });
            const result = await response.text();
            try{
                const json = JSON.parse(result);
                if (json['rst'] === true) {
                    messageApi.open({
                        type: 'success',
                        content: 'Delete successfully!'
                    })

                }
                else {
                    messageApi.open({
                        type: 'warning',
                        content: <>Delete failed: {json['error']}</>
                    })
                }

                onRefreshButtonClick();
            }
            catch(error) {
                const e = error as Error;
                messageApi.open({
                    type: 'error',
                    content: <>Error happened when processing data: {e.message}</>
                })
            }
        }
        catch (error) {
            const e = error as Error;
            messageApi.open({
                type: 'error',
                content: <>Error happened when fetch {config.host + '/delete_json'}: {e.message}</>
            })
        }
    };

    const convertJsonToSeasonInfo = (obj:any) => {
        if (!('name' in obj)) {
            return undefined
        }

        if (!('list' in obj)) {
            return undefined
        }

        var list:string[] = [];
        for (let key in obj['list']) {
            if (obj['list'].hasOwnProperty(key)) {
                list.push(key)
            }
        }

        return {
            key: obj['name'],
            label: obj['name'],
            children: <ul>{list.map((val, index) => <li key={val}>{val}</li>)}</ul>,
            extra: <Popconfirm
                title="Delete the file"
                description="Are you sure to delete this file?"
                onConfirm={onDeleteConfirmClick}
                okText="Yes"
                cancelText="No"
                okButtonProps={{id: 'del-'+obj['name']}}
            >
                <DeleteOutlined
                    onClick={(event) => {
                        event.stopPropagation();
                    }}
                />
            </Popconfirm>,
        }
    }
    
    const onRefreshButtonClick = async () => {
        try {
            const response = await fetch(config.host + '/read_json');
            const result = await response.text();
            try{
                const json = JSON.parse(result);
                var rst:CollapseProps['items'] = [];
                if (json['rst'] !== true) {
                    messageApi.open({
                        type: 'warning',
                        content: <>Referesh failed: {json['error']}</>
                    })
                }
                else {
                    for(const element of json['data']) {
                        var item = convertJsonToSeasonInfo(element)
                        if (item) {
                            rst.push(item)
                        }
                    }
                    setShowInfo(rst)
                }

            }
            catch(error) {
                const e = error as Error;
                messageApi.open({
                    type: 'error',
                    content: <>Error happened when processing data: {e.message}</>
                })
            }
        }
        catch (error) {
            const e = error as Error;
            messageApi.open({
                type: 'error',
                content: <>Error happened when fetch {config.host + '/read_json'}: {e.message}</>
            })
        }
    }

    return (
        <>
                    {contextHolder}
                    <Button type="primary" shape="circle" icon={<ReloadOutlined />} onClick={onRefreshButtonClick} />
                    <Collapse
                        defaultActiveKey={['1']}
                        onChange={onChange}
                        expandIconPosition={'start'}
                        items={showInfo}
                        style={{textAlign:"left"}}
                    />
                </>
    );
};

export default WatchList;